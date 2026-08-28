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

    # Dynamic thematic focus based on question number
    INTERVIEW_THEMES = [
        "Introduction, elevator pitch, and background summary",
        "Technical depth, key tools, and solving complex domain challenges",
        "Behavioral scenario, collaboration, handling feedback, or cross-functional teamwork",
        "Problem-solving under pressure, dealing with ambiguity, tight deadlines, or difficult trade-offs",
        "Leadership, continuous learning, mentoring others, and future career vision"
    ]

    MEETING_THEMES = [
        "Project status briefing, standup update, and milestone recap",
        "Proposing a technical or strategic approach and explaining trade-offs to stakeholders",
        "Addressing client or stakeholder pushback, scope changes, and budget or timeline concerns",
        "Cross-functional coordination with product, design, or business teams",
        "Meeting summary, action items assignment, and defining next milestones"
    ]

    def generate_question(
        self,
        role: str,
        industry: str,
        mode: str = 'interview',
        previous_questions: Optional[List[str]] = None,
        question_number: int = 1
    ) -> Dict:
        """
        Generate a unique, role-specific question that avoids repeating previous questions.
        """
        previous_questions = previous_questions or []
        themes = self.INTERVIEW_THEMES if mode == 'interview' else self.MEETING_THEMES
        theme = themes[(question_number - 1) % len(themes)]

        # 1. Try Gemini AI Generation with strict anti-repetition instructions
        if self.gemini_api_key:
            try:
                client = _get_genai_client(self.gemini_api_key)
                if client:
                    previous_str = "\n".join([f"- {q}" for q in previous_questions]) if previous_questions else "None (this is the first question)"
                    prompt = f"""You are an elite executive interview coach and workplace communication evaluator.
Generate Question #{question_number} for a {mode} practice session.

Position: {role}
Industry: {industry}
Session Mode: {mode.capitalize()}
Question Topic Focus: {theme}

PREVIOUSLY ASKED QUESTIONS IN THIS SESSION (DO NOT REPEAT OR PARAPHRASE THESE):
{previous_str}

REQUIREMENTS:
1. The question MUST be realistic, specific, and directly relevant to a {role} in the {industry} sector.
2. The question MUST focus on: {theme}.
3. The question MUST NOT duplicate or cover the same topic as the previous questions listed above.
4. Return ONLY the question text itself. Do not include question numbers, quotes, prefixes, or conversational remarks."""

                    question = _gemini_text(client, prompt)
                    if question:
                        clean_q = question.strip().strip('"').strip("'")
                        # Verify it is not a direct duplicate
                        if not any(clean_q.lower() == prev.lower().strip() for prev in previous_questions):
                            Logger.info(f"Generated Question #{question_number} via Gemini ({theme}): {clean_q}")
                            return {'success': True, 'question': clean_q, 'source': 'gemini'}
            except Exception as e:
                Logger.warning(f"Gemini question generation error: {e}")

        # 2. Fallback to rich question bank (filtering out already asked questions)
        fallback_pool = self._get_fallback_questions(role, industry, mode, question_number)
        unasked = [q for q in fallback_pool if not any(q.lower().strip() == prev.lower().strip() for prev in previous_questions)]

        if unasked:
            import random
            selected = random.choice(unasked)
            Logger.info(f"Generated Question #{question_number} from fallback pool: {selected}")
            return {'success': True, 'question': selected, 'source': 'database'}

        # Emergency fallback if all bank questions were exhausted
        generic_fallbacks = [
            f"As a {role}, what is your approach to prioritizing competing demands during a busy sprint?",
            f"Can you describe a time in {industry} where you had to adapt quickly to an unexpected change?",
            f"How do you ensure clear and effective communication when collaborating across different teams?",
            f"What methods do you use to measure the success and quality of your work as a {role}?",
            f"What is one key industry trend in {industry} that you believe will impact your role in the next few years?"
        ]
        unasked_generic = [q for q in generic_fallbacks if not any(q.lower().strip() == prev.lower().strip() for prev in previous_questions)]
        chosen = unasked_generic[0] if unasked_generic else generic_fallbacks[(question_number - 1) % len(generic_fallbacks)]

        return {'success': True, 'question': chosen, 'source': 'generic_fallback'}

    def _get_fallback_questions(self, role: str, industry: str, mode: str, question_number: int = 1) -> List[str]:
        """Rich fallback question repository organized by role, mode, and category."""
        bank = {
            'Software Engineer': {
                'interview': [
                    "Can you give me an overview of your software engineering background and the tech stacks you enjoy working with most?",
                    "Tell me about a challenging technical bug or architectural problem you solved recently. How did you diagnose it?",
                    "How do you approach code reviews and giving constructive feedback to peers?",
                    "Describe a time when you had to make a trade-off between delivering code quickly versus maintaining clean architecture.",
                    "How do you stay up-to-date with emerging technologies and decide when to adopt a new tool or framework?",
                    "How do you handle technical debt in a fast-paced environment?",
                    "Describe an experience where requirements were ambiguous. How did you clarify what needed to be built?",
                    "What strategies do you use for optimizing application performance and scalability?"
                ],
                'meeting': [
                    "Could you give us a quick status update on your current sprint deliverables and any blockers you're facing?",
                    "How would you explain the architectural trade-offs of microservices vs monoliths to non-technical stakeholders?",
                    "A client is requesting an urgent out-of-scope feature. How do you address this in our sprint planning meeting?",
                    "How do we coordinate our API changes with the mobile and frontend teams to avoid breaking changes?",
                    "Let's summarize the key takeaways and assign owners for the action items discussed today."
                ]
            },
            'Product Manager': {
                'interview': [
                    "Walk me through your background as a Product Manager and how you prioritize your product roadmap.",
                    "Tell me about a time you had to sunset a feature or pivot a product based on user analytics.",
                    "How do you manage disagreements between engineering estimates and business deadlines?",
                    "Describe a situation where a product launch did not go as expected. What did you learn?",
                    "What is your framework for defining and measuring product-market fit?"
                ],
                'meeting': [
                    "Can you walk the executive team through the key product metrics and user engagement trends this quarter?",
                    "How are we addressing customer feedback regarding the latest feature release in this sync?",
                    "Engineering reported a potential delay on the next milestone. How do we realign expectations with stakeholders?",
                    "What are the top three priorities we must commit to for next sprint's roadmap?",
                    "Let's wrap up with agreed action items and deliverables for each team lead."
                ]
            },
            'Data Analyst': {
                'interview': [
                    "Can you summarize your experience in data analysis, modeling, and visualization tools?",
                    "Tell me about a complex dataset you cleaned and analyzed that produced actionable business insights.",
                    "How do you explain statistical findings or complex charts to stakeholders who are not data-savvy?",
                    "Describe a time when data contradicted a stakeholder's initial hypothesis. How did you present your findings?",
                    "What data validation techniques do you use to ensure data integrity and avoid bias in your reporting?"
                ],
                'meeting': [
                    "Could you present the key insights from last month's performance dashboard to the team?",
                    "How should we address the data anomalies observed in the recent conversion funnel report?",
                    "Stakeholders are asking for automated reporting. What is your proposed implementation plan?",
                    "How do we collaborate with the data engineering team to resolve current data pipeline latency?",
                    "Let's confirm the next steps and deadlines for finalizing the quarterly analytics report."
                ]
            }
        }

        # Role-specific lookup
        if role in bank and mode in bank[role]:
            return bank[role][mode]

        # General high-quality question bank across all other roles
        if mode == 'interview':
            return [
                f"Tell me about your professional journey as a {role} and what brings you to this opportunity in {industry}.",
                f"What is the most significant project you have delivered as a {role}, and what was your specific contribution?",
                "Can you describe a time when you received critical feedback? How did you respond and what changes did you make?",
                "Tell me about a time when you had to balance multiple tight deadlines. How did you prioritize your workload?",
                f"Where do you see yourself growing professionally in {industry} over the next few years?",
                "Describe a situation where you had to persuade a team member or stakeholder to adopt your idea.",
                "Tell me about a time you made a mistake at work. How did you take ownership and resolve it?",
                f"What qualities do you believe are essential for someone to succeed as a {role} in today's {industry} landscape?"
            ]
        else:
            return [
                f"Could you kick off the meeting with a concise update on the progress of our current {role} initiatives?",
                f"We are evaluating a new strategy for our {industry} projects. What are your recommendations?",
                "How should we respond to the latest client feedback to ensure we meet their expectations?",
                "What dependencies between our team and partner departments do we need to address today?",
                "Let's review the agreed action items, assign responsible owners, and set deadlines before closing."
            ]


# ---------------------------------------------------------------------------
def get_speech_service():     return SpeechToTextService()
def get_grammar_service():    return GrammarCheckService()
def get_pronunciation_service(): return PronunciationAnalysisService()
def get_question_service():   return QuestionGenerationService()