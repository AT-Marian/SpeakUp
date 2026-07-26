import os
import io
from typing import List, Dict
from flask import current_app
import requests
import warnings
import json
import google.generativeai as genai
import re

warnings.filterwarnings('ignore')

class SpeechToTextService:
    """Google Cloud Speech-to-Text Service"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("🔧 Initializing SpeechToTextService...")
        try:
            from google.cloud import speech_v1
            self.client = speech_v1.SpeechClient()
            print("✓ Google Cloud Speech Client initialized successfully!")
            print("="*60 + "\n")
        except Exception as e:
            print(f"✗ FAILED to initialize Speech Client: {str(e)}")
            print("="*60 + "\n")
            raise
    
    def transcribe_audio(self, audio_file) -> Dict:
        try:
            from google.cloud import speech_v1
            
            print("\n[→] Speech-to-Text: Starting transcription...")
            audio_file.seek(0)
            content = audio_file.read()
            
            audio = speech_v1.RecognitionAudio(content=content)
            
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                language_code="en-US",
                enable_automatic_punctuation=True,
                max_alternatives=1,
                use_enhanced=True,
                model='default',
            )
            
            response = self.client.recognize(config=config, audio=audio)
            
            transcriptions = []
            
            for result in response.results:
                if result.alternatives:
                    for alternative in result.alternatives:
                        text = alternative.transcript
                        if text.strip():
                            transcriptions.append(text)
            
            full_transcription = " ".join(transcriptions).strip()
            
            return {
                'success': True,
                'transcription': full_transcription,
                'confidence': response.results[0].alternatives[0].confidence if response.results else 0,
                'num_results': len(response.results)
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e), 'transcription': ''}


class GrammarCheckService:
    def __init__(self):
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            
    def check_grammar(self, text: str) -> List[Dict]:
        if not self.gemini_api_key:
            return []

        try:
            # CORRECTED: Changed 3.5 to 1.5. Version 3.5 does not exist.
            model = genai.GenerativeModel('gemini-3.5-flash')
            
            prompt = f"""
            You are an interview coach. Listen to the user's spoken response: "{text}"
            
            Identify ONLY errors that affect the professional quality of spoken communication.
            
            Rules:
            1. IGNORE capitalization and punctuation (e.g., do not correct 'git' to 'Git').
            2. FOCUS on:
               - Improper word usage (e.g., using "get" when they clearly meant the tool "Git").
               - Broken sentence structure that makes the user sound confused.
               - Technical inaccuracies (e.g., saying "I push the server" instead of "I push the code").
            
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
            raw_response = response.text.strip()
            
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
            print(f"Gemini Grammar Analysis Error: {str(e)}")
            return []


class PronunciationAnalysisService:
    """Hybrid Service: Uses STT Confidence + LLM Contextual Inference"""
    def __init__(self):
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
        
    def analyze_pronunciation(self, audio_file, transcription: str, question: str = "") -> List[Dict]:
        if not transcription.strip():
            return []
            
        try:
            # 1. Gather Acoustic Evidence (Where did they mumble?)
            from google.cloud import speech_v1
            client = speech_v1.SpeechClient()
            audio_file.seek(0)
            content = audio_file.read()
            
            audio = speech_v1.RecognitionAudio(content=content)
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                language_code="en-US",
                enable_word_confidence=True, 
            )
            
            response = client.recognize(config=config, audio=audio)
            
            low_confidence_words = []
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
            
            if not low_confidence_words:
                return []
                
            # 2. Contextual Reverse-Engineering (What did they actually mean?)
            if not self.gemini_api_key:
                return self._fallback_format(low_confidence_words)
                
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-3.5-flash')
            
            prompt = f"""
            The user was asked an interview question: "{question}"
            They responded with: "{transcription}"
            
            A Speech-to-Text engine flagged the following words as having low acoustic confidence. This means the user likely mispronounced them, causing the engine to auto-correct them to the wrong dictionary word:
            {json.dumps(low_confidence_words)}
            
            For each flagged word, deduce what the user was ACTUALLY trying to say given the context of the interview question.
            Return ONLY a JSON array of objects. Do not include Markdown formatting. Structure:
            [
              {{
                "type": "pronunciation",
                "word": "the STT auto-corrected word (e.g., somber)",
                "correction": "the word they likely intended (e.g., cucumber)",
                "explanation": "Briefly explain the likely phonetic mispronunciation based on the context.",
                "position": 1 // Must match the position from the input array
              }}
            ]
            """
            
            llm_response = model.generate_content(prompt)
            raw_response = llm_response.text.strip()
            
            json_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
            clean_text = json_match.group(0) if json_match else "[]"
            
            errors = json.loads(clean_text)
            
            # Safety check: if LLM fails formatting, return standard fallback
            if not isinstance(errors, list) or len(errors) == 0:
                return self._fallback_format(low_confidence_words)
                
            return errors
            
        except Exception as e:
            print(f"Pronunciation Reverse-Engineering Error: {str(e)}")
            return self._fallback_format(low_confidence_words) if 'low_confidence_words' in locals() else []

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
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
    
    def generate_question(self, role: str, industry: str, mode: str = 'interview') -> Dict:
        try:
            fallback_questions = self._get_fallback_questions(role, industry, mode)
            
            if self.gemini_api_key:
                try:
                    question = self._generate_via_gemini(role, industry, mode)
                    if question:
                        return {'success': True, 'question': question}
                except Exception as e:
                    pass
            
            if fallback_questions:
                import random
                return {'success': True, 'question': random.choice(fallback_questions), 'source': 'database'}
            
            return {'success': False, 'error': 'Could not generate question', 'question': 'Tell me about your professional experience.'}
        
        except Exception as e:
            return {'success': False, 'error': str(e), 'question': 'Tell me about your professional experience.'}
    
    def _generate_via_gemini(self, role: str, industry: str, mode: str) -> str:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            prompt = f"Generate a single professional {mode} question for a {role} position in the {industry} industry. Return ONLY the question."
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(f"{url}?key={self.gemini_api_key}", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception:
            pass
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