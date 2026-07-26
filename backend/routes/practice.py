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
        
        # Create session
        session = Session(db, user_id, mode, role, industry)
        session_id = session.create()
        
        # Get question service
        question_service = get_question_service()
        question_response = question_service.generate_question(role, industry, mode)
        
        Logger.info(f"Session created: {session_id}, mode: {mode}")
        Logger.info(f"First question: {question_response['question']}")
        
        return generate_response(
            True, 
            'Session started', 
            {
                'session_id': session_id, 
                'question': question_response['question'],
                'mode': mode  # ← RETURN MODE BACK TO FRONTEND
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
    print("\n" + "="*60)
    print("🟢 STARTING AUDIO ANALYSIS")
    print("="*60)
    
    try:
        user_id = get_jwt_identity()
        print("[✓] Step 1: User authenticated")
        
        # Check audio file
        if 'audio' not in request.files:
            print("[✗] Step 2 FAILED: No audio file in request.files")
            return generate_response(False, 'No audio file provided', None, 400)
        
        audio_file = request.files['audio']
        print(f"[✓] Step 2: Audio file received: {audio_file.filename}")
        
        # Get other form data
        question = request.form.get('question', 'No question provided')
        session_id = request.form.get('session_id')
        
        print(f"[✓] Step 3: Question: {question}")
        print(f"[✓] Step 3: Session ID: {session_id}")
        
        # Initialize services
        print("[→] Step 4: Initializing AI Services...")
        speech_service = get_speech_service()
        grammar_service = get_grammar_service()
        pronunciation_service = get_pronunciation_service()
        print("[✓] Step 4: Services Initialized")
        
        # Transcribe audio
        print("[→] Step 5: Sending to Speech-to-Text Service...")
        transcript_result = speech_service.transcribe_audio(audio_file)
        
        if not transcript_result.get('success'):
            error_msg = transcript_result.get('error', 'Unknown error')
            print(f"[✗] Step 5 FAILED: {error_msg}")
            return generate_response(False, 'Failed to transcribe audio', {'error': error_msg}, 500)
        
        transcription = transcript_result.get('transcription', '')
        
        if not transcription or transcription.strip() == '':
            print("[⚠] WARNING: Transcription is EMPTY!")
            transcription = ""
        else:
            print(f"[✓] Step 5 Success: Transcription = '{transcription}'")
        
        # Check grammar
        print("[→] Step 6: Checking Grammar...")
        grammar_errors = grammar_service.check_grammar(transcription) if transcription.strip() else []
        print(f"[✓] Step 6: Found {len(grammar_errors)} grammar errors")
        
        # Check pronunciation
        print("[→] Step 7: Checking Pronunciation...")
        audio_file.seek(0)
        pronunciation_errors = pronunciation_service.analyze_pronunciation(audio_file, transcription, question) if transcription.strip() else []
        print(f"[✓] Step 7: Found {len(pronunciation_errors)} pronunciation errors")
        
        all_errors = grammar_errors + pronunciation_errors
        
        # Update database AND store response
        print("[→] Step 8: Updating Database and storing response...")
        if session_id:
            session_doc = Session.find_by_id(db, session_id)
            if session_doc:
                # 1. Initialize the object
                session = Session(db, user_id, session_doc['mode'], session_doc['role'], session_doc['industry'])
                
                # 2. CRITICAL FIX: Restore the original start time and past responses BEFORE doing math!
                session.started_at = session_doc.get('started_at', session.started_at)
                session.responses = session_doc.get('responses', [])
                
                # 3. Add the new stats to the existing stats
                session.grammar_errors = session_doc.get('grammar_errors', 0) + len(grammar_errors)
                session.pronunciation_errors = session_doc.get('pronunciation_errors', 0) + len(pronunciation_errors)
                session.total_errors = session_doc.get('total_errors', 0) + len(all_errors)
                
                new_words = len(transcription.split()) if transcription.strip() else 0
                session.total_words = session_doc.get('total_words', 0) + new_words
                session.questions_answered = session_doc.get('questions_answered', 0) + 1
                
                # 4. Create the new response entry
                response_data = {
                    'timestamp': datetime.utcnow(),
                    'question': question,
                    'transcription': transcription,
                    'errors': all_errors,
                    'grammar_errors': len(grammar_errors),
                    'pronunciation_errors': len(pronunciation_errors),
                    'accuracy': max(0, 100 - (len(all_errors) * 100 / max(1, len(transcription.split())))) if transcription.strip() else 100
                }
                
                # 5. Append it to our preserved responses array
                session.responses.append(response_data)
                
                # 6. Save EVERYTHING at once. 
                # (You no longer need the extra db['practice_sessions'].update_one with $push!)
                session.save(session_id)
                print("[✓] Step 8: Response stored and session updated safely")
        
        accuracy = 100 if not transcription.strip() else max(0, 100 - (len(all_errors) * 100 / max(1, len(transcription.split()))))
        
        print("\n" + "="*60)
        print("🟢 ANALYSIS COMPLETE")
        print("="*60 + "\n")
        
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
        print("\n" + "="*60)
        print("🔴 CRASH IN ANALYZE ROUTE")
        print("="*60)
        traceback.print_exc()
        print("="*60 + "\n")
        return generate_response(False, 'Analysis failed', None, 500)


@practice_bp.route('/next-question', methods=['POST'])
@jwt_required()
def get_next_question():
    """Get next practice question"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        session_id = data.get('session_id')
        
        print(f"\n[→] Getting next question for session: {session_id}")
        
        session_doc = Session.find_by_id(db, session_id)
        if not session_doc:
            return generate_response(False, 'Session not found', None, 404)
        
        question_service = get_question_service()
        question_response = question_service.generate_question(
            session_doc['role'], 
            session_doc['industry'], 
            session_doc['mode']
        )
        
        print(f"[✓] Next question: {question_response['question']}")
        
        return generate_response(
            True, 
            'Question generated', 
            {'question': question_response['question']}, 
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
    print("\n" + "="*70)
    print("🟢 FINISHING SESSION ENDPOINT")
    print("="*70)
    
    try:
        user_id = get_jwt_identity()
        print(f"[✓] User ID: {user_id}")
        
        data = request.get_json()
        session_id = data.get('session_id')
        
        print(f"[✓] Session ID from request: {session_id}")
        
        if not session_id:
            print("[✗] No session ID provided")
            return generate_response(False, 'Session ID required', None, 400)
        
        # Fetch the session document from database
        print(f"[→] Finding session: {session_id}")
        session_doc = Session.find_by_id(db, session_id)
        
        if not session_doc:
            print("[✗] Session not found in database")
            return generate_response(False, 'Session not found', None, 404)
        
        print(f"[✓] Session found")
        print(f"    Started at: {session_doc.get('started_at')}")
        print(f"    Ended at: {session_doc.get('ended_at')}")
        print(f"    Questions answered: {session_doc.get('questions_answered')}")
        print(f"    Duration (existing): {session_doc.get('duration_seconds')} seconds")
        
        # Calculate duration NOW
        started = session_doc.get('started_at')
        now = datetime.utcnow()
        
        if started:
            duration = (now - started).total_seconds()
            print(f"[✓] Duration calculated: {int(duration)} seconds")
        else:
            duration = 0
            print("[⚠] No start time found")
        
        # Create update data
        update_data = {
            'ended_at': now,
            'duration_seconds': int(duration)
        }
        
        print(f"\n[→] Updating session with:")
        print(f"    ended_at: {now}")
        print(f"    duration_seconds: {int(duration)}")
        
        # Update the session in MongoDB
        result = db['practice_sessions'].update_one(
            {'_id': ObjectId(session_id)},
            {'$set': update_data}
        )
        
        print(f"[✓] Update result - Matched: {result.matched_count}, Modified: {result.modified_count}")
        
        # Verify the update by re-fetching
        print(f"\n[→] Verifying update by re-fetching session...")
        updated_session = Session.find_by_id(db, session_id)
        
        if updated_session:
            print(f"[✓] Session re-fetched:")
            print(f"    Ended at: {updated_session.get('ended_at')}")
            print(f"    Duration: {updated_session.get('duration_seconds')} seconds")
            print(f"    Responses count: {len(updated_session.get('responses', []))}")
        else:
            print("[✗] Could not re-fetch session")
        
        # Generate summary
        print(f"\n[→] Generating summary...")
        summary = get_session_summary(updated_session if updated_session else session_doc)
        
        print(f"[✓] Summary generated:")
        print(f"    {summary}")
        
        print("\n" + "="*70)
        print("✅ SESSION FINISH COMPLETE")
        print("="*70 + "\n")
        
        return generate_response(
            True, 
            'Session completed', 
            {'summary': summary}, 
            200
        )
    
    except Exception as e:
        print("\n" + "="*70)
        print("🔴 ERROR IN finish_session")
        print("="*70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
        
        return generate_response(False, f'Failed to finish session: {str(e)}', None, 500)


@practice_bp.route('/add-response', methods=['POST'])
@jwt_required()
def add_response():
    """Add response to session (optional endpoint for storing responses)"""
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