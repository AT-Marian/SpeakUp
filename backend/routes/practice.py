from flask import Blueprint, request, jsonify
import traceback
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from models.session import Session
from models.user import User
from utils.validators import token_required, validate_audio_file
from utils.helpers import generate_response, serialize_mongo_doc, get_session_summary, Logger
from utils.ai_services import (
    get_speech_service, get_grammar_service, get_pronunciation_service, get_question_service
)
import os
import tempfile

practice_bp = Blueprint('practice', __name__, url_prefix='/api/practice')

# MongoDB database instance
db = None

def set_database(database):
    global db
    db = database

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'webm', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@practice_bp.route('/start', methods=['POST'])
@jwt_required()
def start_session():
    """Start a practice session"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        mode = data.get('mode', 'interview')
        role = data.get('role', 'Software Engineer')
        industry = data.get('industry', 'Technology')
        
        Logger.info(f"Starting session: mode={mode}, role={role}, industry={industry}")
        
        if not mode or not role or not industry:
            return generate_response(False, 'Missing required fields', None, 400)
        
        if mode not in ['interview', 'meeting']:
            return generate_response(False, 'Invalid practice mode', None, 400)
        
        # Get question service
        question_service = get_question_service()
        question_response = question_service.generate_question(
            role=role, 
            industry=industry, 
            mode=mode,
            previous_questions=[],
            question_number=1
        )
        first_question = question_response.get('question', 'Tell me about your professional experience.')
        
        # Create session with the first question recorded
        session = Session(db, user_id, mode, role, industry)
        session.questions = [first_question]
        session_id = session.create()
        
        Logger.info(f"Session created: {session_id}, mode: {mode}")
        Logger.info(f"First question (Q1): {first_question}")
        
        return generate_response(
            True, 
            'Session started', 
            {
                'session_id': session_id, 
                'question': first_question,
                'mode': mode
            }, 
            200
        )
    
    except Exception as e:
        Logger.error(f"Start session error: {str(e)}")
        traceback.print_exc()
        return generate_response(False, 'Failed to start session', None, 500)


@practice_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_response():
    """Analyze user response (audio + transcription) and store in session"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    Logger.info("Starting Audio Analysis...")
    
    try:
        user_id = get_jwt_identity()
        
        # Check audio file
        if 'audio' not in request.files:
            Logger.warning("No audio file in request.files")
            return generate_response(False, 'No audio file provided', None, 400)
        
        audio_file = request.files['audio']
        Logger.info(f"Audio file received: {audio_file.filename}")
        
        # Get other form data
        question = request.form.get('question', 'No question provided')
        session_id = request.form.get('session_id')
        
        Logger.info(f"Question: {question}")
        Logger.info(f"Session ID: {session_id}")
        
        # Initialize services
        speech_service = get_speech_service()
        grammar_service = get_grammar_service()
        pronunciation_service = get_pronunciation_service()
        
        # Transcribe audio
        Logger.info("Sending to Speech-to-Text Service...")
        transcript_result = speech_service.transcribe_audio(audio_file)
        
        transcription = transcript_result.get('transcription', '') if transcript_result else ''
        if not transcription or not transcription.strip():
            Logger.warning("Transcription is empty — no speech detected in audio")
            return generate_response(False, 'No speech detected. Please speak clearly and try again.', None, 400)
        else:
            Logger.info(f"Transcription: {transcription}")
        
        # Check grammar
        grammar_errors = []
        try:
            grammar_errors = grammar_service.check_grammar(transcription) if transcription.strip() else []
        except Exception as ge:
            Logger.warning(f"Grammar check failed: {str(ge)}")
            
        Logger.info(f"Found {len(grammar_errors)} grammar errors")
        
        # Check pronunciation
        pronunciation_errors = []
        try:
            audio_file.seek(0)
            pronunciation_errors = pronunciation_service.analyze_pronunciation(audio_file, transcription, question) if transcription.strip() else []
        except Exception as pe:
            Logger.warning(f"Pronunciation check failed: {str(pe)}")
            
        Logger.info(f"Found {len(pronunciation_errors)} pronunciation errors")
        
        all_errors = grammar_errors + pronunciation_errors
        
        # Update database AND store response
        if session_id:
            try:
                session_doc = Session.find_by_id(db, session_id)
                if session_doc:
                    session = Session(db, user_id, session_doc['mode'], session_doc['role'], session_doc['industry'])
                    
                    session.started_at = session_doc.get('started_at', session.started_at)
                    session.responses = session_doc.get('responses', [])
                    
                    session.grammar_errors = session_doc.get('grammar_errors', 0) + len(grammar_errors)
                    session.pronunciation_errors = session_doc.get('pronunciation_errors', 0) + len(pronunciation_errors)
                    session.total_errors = session_doc.get('total_errors', 0) + len(all_errors)
                    
                    new_words = len(transcription.split()) if transcription.strip() else 0
                    session.total_words = session_doc.get('total_words', 0) + new_words
                    session.questions_answered = session_doc.get('questions_answered', 0) + 1
                    
                    response_data = {
                        'timestamp': datetime.utcnow(),
                        'question': question,
                        'transcription': transcription,
                        'errors': all_errors,
                        'grammar_errors': len(grammar_errors),
                        'pronunciation_errors': len(pronunciation_errors),
                        'accuracy': max(0, 100 - (len(all_errors) * 100 / max(1, len(transcription.split())))) if transcription.strip() else 100
                    }
                    
                    session.responses.append(response_data)
                    session.save(session_id)
                    Logger.info("Response stored and session updated safely")
            except Exception as dbe:
                Logger.error(f"Failed to update session doc in DB: {str(dbe)}")
        
        accuracy = 100 if not transcription.strip() else max(0, 100 - (len(all_errors) * 100 / max(1, len(transcription.split()))))
        
        Logger.info("Audio Analysis Complete")
        
        return generate_response(
            True, 
            'Analysis complete', 
            {
                'transcription': transcription, 
                'errors': all_errors,
                'accuracy': accuracy
            }, 
            200
        )
    
    except Exception as e:
        Logger.error(f"Error in analyze route: {str(e)}")
        traceback.print_exc()
        return generate_response(False, f'Analysis failed: {str(e)}', None, 500)


@practice_bp.route('/next-question', methods=['POST'])
@jwt_required()
def get_next_question():
    """Get next practice question"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        session_id = data.get('session_id')
        
        Logger.info(f"Getting next question for session: {session_id}")
        
        session_doc = Session.find_by_id(db, session_id)
        if not session_doc:
            return generate_response(False, 'Session not found', None, 404)
        
        # Collect all previously asked questions in this session
        previous_questions = []
        for resp in session_doc.get('responses', []):
            if resp.get('question'):
                previous_questions.append(resp.get('question'))
        for q in session_doc.get('questions', []):
            if q not in previous_questions:
                previous_questions.append(q)

        question_number = len(previous_questions) + 1
        
        question_service = get_question_service()
        question_response = question_service.generate_question(
            role=session_doc.get('role', 'Software Engineer'), 
            industry=session_doc.get('industry', 'Technology'), 
            mode=session_doc.get('mode', 'interview'),
            previous_questions=previous_questions,
            question_number=question_number
        )
        new_question = question_response.get('question', 'Tell me about your professional experience.')
        
        # Save newly generated question into the session document
        try:
            db['practice_sessions'].update_one(
                {'_id': ObjectId(session_id)},
                {'$addToSet': {'questions': new_question}}
            )
        except Exception as dbe:
            Logger.warning(f"Could not update questions array in session: {dbe}")

        Logger.info(f"Next question (Q{question_number}): {new_question}")
        
        return generate_response(
            True, 
            'Question generated', 
            {'question': new_question, 'question_number': question_number}, 
            200
        )
    except Exception as e:
        Logger.error(f"Get next question error: {str(e)}")
        traceback.print_exc()
        return generate_response(False, 'Failed to generate question', None, 500)


@practice_bp.route('/finish', methods=['POST'])
@jwt_required()
def finish_session():
    """Finish practice session and calculate final stats"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    Logger.info("Finishing session endpoint")
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        session_id = data.get('session_id') if data else None
        
        if not session_id:
            return generate_response(False, 'Session ID required', None, 400)
        
        session_doc = Session.find_by_id(db, session_id)
        if not session_doc:
            return generate_response(False, 'Session not found', None, 404)
        
        started = session_doc.get('started_at')
        now = datetime.utcnow()
        duration = int((now - started).total_seconds()) if started else 0
        
        update_data = {
            'ended_at': now,
            'duration_seconds': duration
        }
        
        db['practice_sessions'].update_one(
            {'_id': ObjectId(session_id)},
            {'$set': update_data}
        )
        
        updated_session = Session.find_by_id(db, session_id)
        summary = get_session_summary(updated_session if updated_session else session_doc)
        
        Logger.info("Session finish complete")
        
        return generate_response(
            True, 
            'Session completed', 
            {'summary': summary}, 
            200
        )
    
    except Exception as e:
        Logger.error(f"Error in finish_session: {str(e)}")
        traceback.print_exc()
        return generate_response(False, f'Failed to finish session: {str(e)}', None, 500)


@practice_bp.route('/add-response', methods=['POST'])
@jwt_required()
def add_response():
    """Add response to session (optional endpoint for storing responses)"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        session_id = data.get('session_id')
        
        response = {
            'timestamp': datetime.utcnow(),
            'question': data.get('question'),
            'transcription': data.get('transcription'),
            'errors': data.get('errors', []),
            'accuracy': data.get('accuracy', 0)
        }
        
        Session.add_response(db, session_id, response)
        
        return generate_response(True, 'Response added', None, 200)
    except Exception as e:
        Logger.error(f"Add response error: {str(e)}")
        return generate_response(False, 'Failed to add response', None, 500)