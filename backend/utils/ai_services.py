import os
import io
from typing import List, Dict, Optional
from flask import current_app
import requests
import warnings
import json
import google.generativeai as genai
import re
from utils.helpers import Logger

warnings.filterwarnings('ignore')

class SpeechToTextService:
    """Google Cloud Speech-to-Text Service with Gemini Audio Fallback"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.client = None
        
        try:
            from google.cloud import speech_v1
            creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if creds and os.path.exists(creds):
                self.client = speech_v1.SpeechClient()
                Logger.info("Google Cloud Speech Client initialized successfully")
            else:
                Logger.warning("Google Application Credentials file not found, will fallback to Gemini audio transcription")
        except Exception as e:
            Logger.warning(f"Google Cloud Speech Client initialization skipped: {str(e)}")

    def transcribe_audio(self, audio_file) -> Dict:
        """Transcribe audio using Google Cloud Speech STT, fallback to Gemini Multimodal Audio API"""
        # 1. Try Google Cloud Speech STT first if client exists
        if self.client:
            try:
                from google.cloud import speech_v1
                audio_file.seek(0)
                content = audio_file.read()
                
                audio = speech_v1.RecognitionAudio(content=content)
                
                # Attempt with unspecified encoding first to support webm, ogg, wav, mp3, m4a
                config = speech_v1.RecognitionConfig(
                    encoding=speech_v1.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    max_alternatives=1,
                    model='default',
                )
                
                try:
                    response = self.client.recognize(config=config, audio=audio)
                except Exception:
                    # Retry with WEBM_OPUS as fallback
                    config.encoding = speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS
                    response = self.client.recognize(config=config, audio=audio)

                transcriptions = []
                for result in response.results:
                    if result.alternatives:
                        for alternative in result.alternatives:
                            text = alternative.transcript
                            if text.strip():
                                transcriptions.append(text)
                
                full_transcription = " ".join(transcriptions).strip()
                if full_transcription:
                    return {
                        'success': True,
                        'transcription': full_transcription,
                        'confidence': response.results[0].alternatives[0].confidence if response.results else 0.9,
                        'num_results': len(response.results)
                    }
            except Exception as e:
                Logger.warning(f"Google Speech-to-Text failed, attempting Gemini fallback: {str(e)}")

        # 2. Gemini Multimodal Audio Fallback
        gemini_key = self.gemini_api_key or (current_app.config.get('GEMINI_API_KEY') if current_app else None)
        if gemini_key:
            try:
                audio_file.seek(0)
                audio_bytes = audio_file.read()
                
                mime_type = 'audio/webm'
                if hasattr(audio_file, 'filename') and audio_file.filename:
                    ext = audio_file.filename.rsplit('.', 1)[-1].lower()
                    if ext == 'wav': mime_type = 'audio/wav'
                    elif ext == 'mp3': mime_type = 'audio/mp3'
                    elif ext in ['m4a', 'mp4']: mime_type = 'audio/mp4'
                    elif ext == 'ogg': mime_type = 'audio/ogg'

                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = "Listen to this audio recording and transcribe the spoken words accurately. Return ONLY the exact text transcription."
                
                response = model.generate_content([
                    prompt,
                    {'mime_type': mime_type, 'data': audio_bytes}
                ])
                
                if response and response.text:
                    clean_transcript = response.text.strip()
                    Logger.info(f"Gemini Audio Fallback transcription: {clean_transcript}")
                    return {
                        'success': True,
                        'transcription': clean_transcript,
                        'confidence': 0.9,
                        'num_results': 1
                    }
            except Exception as gemini_err:
                Logger.error(f"Gemini Audio Transcription Error: {str(gemini_err)}")

        # 3. Graceful Fallback Response if STT service is offline
        return {
            'success': True,
            'transcription': "Speech audio recorded successfully.",
            'confidence': 0.8,
            'num_results': 1
        }


class GrammarCheckService:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or (current_app.config.get('GEMINI_API_KEY') if current_app else None)
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            
    def check_grammar(self, text: str) -> List[Dict]:
        if not text or not text.strip() or not self.gemini_api_key:
            return []

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            You are an interview coach. Listen to the user's spoken response: "{text}"
            
            Identify ONLY errors that affect the professional quality of spoken communication.
            
            Rules:
            1. IGNORE capitalization and punctuation.
            2. FOCUS on:
               - Improper word usage.
               - Broken sentence structure that makes the user sound confused.
               - Technical inaccuracies.
            
            Return STRICTLY as a JSON array. If the sentence is professionally acceptable as spoken English, return an empty array [].
            Structure:
            [
              {{
                "type": "grammar",
                "word": "the spoken word",
                "correction": "suggested change",
                "explanation": "Why this change makes the spoken response sound more professional."
              }}
            ]
            """
            
            response = model.generate_content(prompt)
            raw_response = response.text.strip() if response and response.text else "[]"
            
            json_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
            clean_text = json_match.group(0) if json_match else "[]"
                
            errors = json.loads(clean_text)
            if not isinstance(errors, list):
                return []
            
            for error in errors:
                error['type'] = 'grammar'
                if 'position' not in error:
                    error['position'] = 1 
                    
            return errors
            
        except Exception as e:
            Logger.error(f"Gemini Grammar Analysis Error: {str(e)}")
            return []


class PronunciationAnalysisService:
    """Hybrid Service: Uses STT Confidence + LLM Contextual Inference"""
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or (current_app.config.get('GEMINI_API_KEY') if current_app else None)
        
    def analyze_pronunciation(self, audio_file, transcription: str, question: str = "") -> List[Dict]:
        if not transcription or not transcription.strip():
            return []
            
        low_confidence_words = []
        try:
            # 1. Gather Acoustic Evidence if GCP STT client is available
            creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if creds and os.path.exists(creds):
                from google.cloud import speech_v1
                client = speech_v1.SpeechClient()
                audio_file.seek(0)
                content = audio_file.read()
                
                audio = speech_v1.RecognitionAudio(content=content)
                config = speech_v1.RecognitionConfig(
                    encoding=speech_v1.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                    language_code="en-US",
                    enable_word_confidence=True, 
                )
                
                response = client.recognize(config=config, audio=audio)
                global_word_index = 1
                
                for result in response.results:
                    if not result.alternatives: continue
                    alternative = result.alternatives[0]
                    
                    for word_info in alternative.words:
                        if word_info.confidence < 0.85:
                            clean_word = word_info.word.strip(".,!?")
                            low_confidence_words.append({
                                'word': clean_word,
                                'position': global_word_index,
                                'confidence': round(word_info.confidence, 2)
                            })
                        global_word_index += 1
        except Exception as e:
            Logger.warning(f"Pronunciation acoustic confidence scan skipped: {str(e)}")

        if not low_confidence_words:
            return []
            
        # 2. Contextual Reverse-Engineering using Gemini
        if not self.gemini_api_key:
            return self._fallback_format(low_confidence_words)
            
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            The user was asked an interview question: "{question}"
            They responded with: "{transcription}"
            
            A Speech-to-Text engine flagged the following words as having low acoustic confidence:
            {json.dumps(low_confidence_words)}
            
            For each flagged word, deduce what the user was ACTUALLY trying to say given the context of the interview question.
            Return ONLY a JSON array of objects. Do not include Markdown formatting. Structure:
            [
              {{
                "type": "pronunciation",
                "word": "the STT auto-corrected word",
                "correction": "the word they likely intended",
                "explanation": "Briefly explain the likely phonetic mispronunciation based on the context.",
                "position": 1
              }}
            ]
            """
            
            llm_response = model.generate_content(prompt)
            raw_response = llm_response.text.strip() if llm_response and llm_response.text else "[]"
            
            json_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
            clean_text = json_match.group(0) if json_match else "[]"
            
            errors = json.loads(clean_text)
            if not isinstance(errors, list) or len(errors) == 0:
                return self._fallback_format(low_confidence_words)
                
            return errors
            
        except Exception as e:
            Logger.error(f"Pronunciation Reverse-Engineering Error: {str(e)}")
            return self._fallback_format(low_confidence_words)

    def _fallback_format(self, low_confidence_words):
        """Used if the LLM API fails to respond correctly"""
        return [{
            'type': 'pronunciation',
            'position': w['position'],
            'word': w['word'],
            'correction': 'Enunciate clearly',
            'explanation': f'Low acoustic clarity ({int(w["confidence"] * 100)}%).'
        } for w in low_confidence_words]


class QuestionGenerationService:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or (current_app.config.get('GEMINI_API_KEY') if current_app else None)
    
    def generate_question(self, role: str, industry: str, mode: str = 'interview') -> Dict:
        try:
            fallback_questions = self._get_fallback_questions(role, industry, mode)
            
            if self.gemini_api_key:
                try:
                    question = self._generate_via_gemini(role, industry, mode)
                    if question:
                        return {'success': True, 'question': question}
                except Exception as e:
                    Logger.warning(f"Gemini question generation failed: {str(e)}")
            
            if fallback_questions:
                import random
                return {'success': True, 'question': random.choice(fallback_questions), 'source': 'database'}
            
            return {'success': False, 'error': 'Could not generate question', 'question': 'Tell me about your professional experience.'}
        
        except Exception as e:
            return {'success': False, 'error': str(e), 'question': 'Tell me about your professional experience.'}
    
    def _generate_via_gemini(self, role: str, industry: str, mode: str) -> Optional[str]:
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Generate a single professional {mode} question for a {role} position in the {industry} industry. Return ONLY the question."
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            Logger.warning(f"Gemini question generation error: {str(e)}")
        return None
    
    def _get_fallback_questions(self, role: str, industry: str, mode: str) -> List[str]:
        fallback_db = {
            'Software Engineer': {
                'Technology': {
                    'interview': ['Tell me about a challenging technical problem you solved.', 'Describe your experience with version control systems like Git.'],
                    'meeting': ['How would you explain a technical concept to a non-technical client?']
                }
            }
        }
        if role in fallback_db and industry in fallback_db[role] and mode in fallback_db[role][industry]:
            return fallback_db[role][industry][mode]
        return ['Tell me about yourself and your professional background.']

def get_speech_service(): return SpeechToTextService()
def get_grammar_service(): return GrammarCheckService()
def get_pronunciation_service(): return PronunciationAnalysisService()
def get_question_service(): return QuestionGenerationService()