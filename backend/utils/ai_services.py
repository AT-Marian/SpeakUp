import os
import io
from typing import List, Dict, Optional
from flask import current_app
import requests
import warnings
import json
import re
from utils.helpers import Logger

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Gemini client helper — uses the NEW google-genai SDK
# ---------------------------------------------------------------------------
GEMINI_MODEL = 'gemini-3.5-flash-lite'   # confirmed working
GEMINI_MODEL_FALLBACKS = [
    'gemini-3.5-flash-lite',
    'gemini-3.6-flash',
    'gemini-2.5-flash-lite-preview-06-17',
    'gemini-2.5-flash',
]

def _get_genai_client(api_key: str):
    """Return a google-genai Client, or None on import failure."""
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        Logger.error(f"Failed to import google-genai: {e}")
        return None

def _gemini_text(client, prompt: str) -> Optional[str]:
    """Call Gemini with a text prompt, trying each model until one succeeds."""
    for model in GEMINI_MODEL_FALLBACKS:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            err = str(e)
            if 'no longer available' in err or 'NOT_FOUND' in err:
                Logger.warning(f"Model {model} unavailable, trying next...")
                continue
            Logger.error(f"Gemini text error with {model}: {type(e).__name__}: {err}")
            return None
    Logger.error("All Gemini models failed for text generation")
    return None

def _gemini_audio(client, audio_bytes: bytes, mime_type: str) -> Optional[str]:
    """Call Gemini with audio inline data, trying each model until one succeeds."""
    try:
        from google.genai import types as genai_types
        part = genai_types.Part(
            inline_data=genai_types.Blob(mime_type=mime_type, data=audio_bytes)
        )
    except Exception:
        part = {'mime_type': mime_type, 'data': audio_bytes}

    prompt = "Listen to this audio recording carefully and transcribe every spoken word accurately. Return ONLY the exact text transcription, nothing else."

    for model in GEMINI_MODEL_FALLBACKS:
        try:
            response = client.models.generate_content(model=model, contents=[prompt, part])
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            err = str(e)
            if 'no longer available' in err or 'NOT_FOUND' in err:
                Logger.warning(f"Model {model} unavailable for audio, trying next...")
                continue
            Logger.error(f"Gemini audio error with {model}: {type(e).__name__}: {err}")
            return None
    Logger.error("All Gemini models failed for audio transcription")
    return None


# ---------------------------------------------------------------------------
class SpeechToTextService:
    """Google Cloud Speech-to-Text with Gemini Audio Fallback (new SDK)"""

    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.cloud_client = None

        try:
            from google.cloud import speech_v1
            creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if creds and os.path.exists(creds):
                self.cloud_client = speech_v1.SpeechClient()
                Logger.info("Google Cloud Speech Client initialized successfully")
            else:
                Logger.warning("GCP credentials not found — will use Gemini audio transcription")
        except Exception as e:
            Logger.warning(f"Google Cloud Speech init skipped: {e}")

    def transcribe_audio(self, audio_file) -> Dict:
        """Transcribe audio: try GCP STT first, then Gemini multimodal."""

        # 1. Google Cloud Speech-to-Text
        if self.cloud_client:
            try:
                from google.cloud import speech_v1
                audio_file.seek(0)
                content = audio_file.read()

                audio = speech_v1.RecognitionAudio(content=content)
                config = speech_v1.RecognitionConfig(
                    encoding=speech_v1.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    max_alternatives=1,
                    model='default',
                )
                try:
                    response = self.cloud_client.recognize(config=config, audio=audio)
                except Exception:
                    config.encoding = speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS
                    response = self.cloud_client.recognize(config=config, audio=audio)

                transcriptions = [
                    alt.transcript
                    for result in response.results
                    for alt in result.alternatives
                    if alt.transcript.strip()
                ]
                full = " ".join(transcriptions).strip()
                if full:
                    Logger.info(f"GCP STT transcription: {full}")
                    return {
                        'success': True,
                        'transcription': full,
                        'confidence': response.results[0].alternatives[0].confidence if response.results else 0.9,
                        'num_results': len(response.results)
                    }
            except Exception as e:
                Logger.warning(f"GCP STT failed, falling back to Gemini: {e}")

        # 2. Gemini Multimodal Audio (new SDK)
        gemini_key = self.gemini_api_key or (current_app.config.get('GEMINI_API_KEY') if current_app else None)
        if gemini_key:
            try:
                audio_file.seek(0)
                audio_bytes = audio_file.read()

                Logger.info(f"Audio bytes received: {len(audio_bytes)} bytes")

                if not audio_bytes or len(audio_bytes) < 100:
                    Logger.warning("Audio blob is empty or too small — skipping Gemini transcription")
                else:
                    # Determine MIME type from filename
                    mime_type = 'audio/webm'
                    if hasattr(audio_file, 'filename') and audio_file.filename:
                        ext = audio_file.filename.rsplit('.', 1)[-1].lower()
                        if ext == 'wav':             mime_type = 'audio/wav'
                        elif ext == 'mp3':           mime_type = 'audio/mp3'
                        elif ext in ['m4a', 'mp4']:  mime_type = 'audio/mp4'
                        elif ext == 'ogg':           mime_type = 'audio/ogg'

                    Logger.info(f"Sending audio to Gemini: mime_type={mime_type}, size={len(audio_bytes)} bytes")

                    client = _get_genai_client(gemini_key)
                    if client:
                        transcript = _gemini_audio(client, audio_bytes, mime_type)
                        if transcript:
                            Logger.info(f"Gemini transcription: {transcript}")
                            return {
                                'success': True,
                                'transcription': transcript,
                                'confidence': 0.9,
                                'num_results': 1
                            }
                        else:
                            Logger.warning("Gemini returned empty transcription for audio")
            except Exception as gemini_err:
                Logger.error(f"Gemini audio transcription error: {type(gemini_err).__name__}: {gemini_err}")

        # 3. All services failed
        Logger.warning("All transcription services failed. Returning empty transcription.")
        return {
            'success': False,
            'transcription': '',
            'confidence': 0.0,
            'num_results': 0
        }


# ---------------------------------------------------------------------------
class GrammarCheckService:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or (current_app.config.get('GEMINI_API_KEY') if current_app else None)

    def check_grammar(self, text: str) -> List[Dict]:
        if not text or not text.strip() or not self.gemini_api_key:
            return []

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
        try:
            client = _get_genai_client(self.gemini_api_key)
            if not client:
                return []
            raw = _gemini_text(client, prompt) or "[]"

            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            clean = json_match.group(0) if json_match else "[]"
            errors = json.loads(clean)
            if not isinstance(errors, list):
                return []

            for err in errors:
                err['type'] = 'grammar'
                if 'position' not in err:
                    err['position'] = 1
            return errors

        except Exception as e:
            Logger.error(f"Grammar check error: {type(e).__name__}: {e}")
            return []


# ---------------------------------------------------------------------------
class PronunciationAnalysisService:
    """Hybrid: GCP STT word-confidence + Gemini contextual inference"""

    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or (current_app.config.get('GEMINI_API_KEY') if current_app else None)

    def analyze_pronunciation(self, audio_file, transcription: str, question: str = "") -> List[Dict]:
        if not transcription or not transcription.strip():
            return []

        low_confidence_words = []
        try:
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
                idx = 1
                for result in response.results:
                    if not result.alternatives:
                        continue
                    for word_info in result.alternatives[0].words:
                        if word_info.confidence < 0.85:
                            low_confidence_words.append({
                                'word': word_info.word.strip(".,!?"),
                                'position': idx,
                                'confidence': round(word_info.confidence, 2)
                            })
                        idx += 1
        except Exception as e:
            Logger.warning(f"Pronunciation acoustic scan skipped: {e}")

        if not low_confidence_words:
            return []

        # Gemini contextual reverse-engineering
        if not self.gemini_api_key:
            return self._fallback_format(low_confidence_words)

        prompt = f"""
The user was asked an interview question: "{question}"
They responded with: "{transcription}"

A Speech-to-Text engine flagged these words as having low acoustic confidence:
{json.dumps(low_confidence_words)}

For each flagged word, deduce what the user was ACTUALLY trying to say given the context.
Return ONLY a JSON array. No Markdown formatting.
[
  {{
    "type": "pronunciation",
    "word": "the STT auto-corrected word",
    "correction": "the word they likely intended",
    "explanation": "Briefly explain the likely phonetic mispronunciation.",
    "position": 1
  }}
]
"""
        try:
            client = _get_genai_client(self.gemini_api_key)
            if not client:
                return self._fallback_format(low_confidence_words)
            raw = _gemini_text(client, prompt) or "[]"

            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            clean = json_match.group(0) if json_match else "[]"
            errors = json.loads(clean)
            if not isinstance(errors, list) or len(errors) == 0:
                return self._fallback_format(low_confidence_words)
            return errors
        except Exception as e:
            Logger.error(f"Pronunciation inference error: {type(e).__name__}: {e}")
            return self._fallback_format(low_confidence_words)

    def _fallback_format(self, low_confidence_words):
        return [{
            'type': 'pronunciation',
            'position': w['position'],
            'word': w['word'],
            'correction': 'Enunciate clearly',
            'explanation': f'Low acoustic clarity ({int(w["confidence"] * 100)}%).'
        } for w in low_confidence_words]


# ---------------------------------------------------------------------------
class QuestionGenerationService:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or (current_app.config.get('GEMINI_API_KEY') if current_app else None)

    def generate_question(self, role: str, industry: str, mode: str = 'interview') -> Dict:
        fallback_questions = self._get_fallback_questions(role, industry, mode)

        if self.gemini_api_key:
            try:
                client = _get_genai_client(self.gemini_api_key)
                if client:
                    prompt = f"Generate a single professional {mode} question for a {role} position in the {industry} industry. Return ONLY the question, no extra text."
                    question = _gemini_text(client, prompt)
                    if question:
                        return {'success': True, 'question': question}
            except Exception as e:
                Logger.warning(f"Gemini question generation failed: {e}")

        if fallback_questions:
            import random
            return {'success': True, 'question': random.choice(fallback_questions), 'source': 'database'}

        return {'success': False, 'error': 'Could not generate question', 'question': 'Tell me about your professional experience.'}

    def _get_fallback_questions(self, role: str, industry: str, mode: str) -> List[str]:
        fallback_db = {
            'Software Engineer': {
                'Technology': {
                    'interview': [
                        'Tell me about a challenging technical problem you solved.',
                        'Describe your experience with version control systems like Git.',
                    ],
                    'meeting': ['How would you explain a technical concept to a non-technical client?']
                }
            }
        }
        if role in fallback_db and industry in fallback_db[role] and mode in fallback_db[role][industry]:
            return fallback_db[role][industry][mode]
        return ['Tell me about yourself and your professional background.']


# ---------------------------------------------------------------------------
def get_speech_service():     return SpeechToTextService()
def get_grammar_service():    return GrammarCheckService()
def get_pronunciation_service(): return PronunciationAnalysisService()
def get_question_service():   return QuestionGenerationService()