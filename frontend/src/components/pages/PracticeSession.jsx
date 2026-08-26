import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FiMic, FiX, FiAlertCircle } from 'react-icons/fi';
import axios from 'axios';

const API_URL = (process.env.REACT_APP_API_URL || 'http://localhost:5000').replace(/\/+$/, '');

export default function PracticeSession() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const sessionData = location.state || {};

  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [question, setQuestion] = useState('Loading question...');
  const [recordingTime, setRecordingTime] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(sessionData.currentQuestion || 1);
  const [totalQuestions] = useState(sessionData.totalQuestions || 5);
  const [sessionId, setSessionId] = useState(sessionData.sessionId || null);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!sessionStarted) {
      if (sessionData.isNextQuestion) {
        // Coming from "Next Question" button
        console.log('Fetching next question...',sessionData.mode);
        fetchNextQuestion();
      } else if (sessionData.isRerecord) {
        // Re-recording same question
        console.log('Re-recording:', sessionData.mode);
        setQuestion(sessionData.question);
        setSessionId(sessionData.sessionId);
        setSessionStarted(true);
      } else {
        // Brand new session from Dashboard
        console.log('Initializing new session with:', {
        mode: sessionData.mode,
        role: sessionData.role,
        industry: sessionData.industry
      });
        initializeSession();
      }
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const initializeSession = async () => {
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setError('You must be logged in to practice');
        navigate('/login');
        return;
      }

      console.log('Starting session with:', {
        mode: sessionData.mode || 'interview',
        role: sessionData.role || 'Software Engineer',
        industry: sessionData.industry || 'Technology'
      });

      const response = await axios.post(
        `${API_URL}/api/practice/start`,
        {
          mode: sessionData.mode || 'interview',
          role: sessionData.role || 'Software Engineer',
          industry: sessionData.industry || 'Technology'
        },
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          timeout: 10000
        }
      );

      console.log('Session started:', response.data);
      setSessionId(response.data.data.session_id);
      setQuestion(response.data.data.question || 'Tell me about yourself');
      setSessionStarted(true);
      setError(null);
    } catch (error) {
      console.error('Failed to start session:', error.response?.data || error.message);
      setError('Could not start practice session. Please check your connection.');
    }
  };

  const fetchNextQuestion = async () => {
    try {
      const token = localStorage.getItem('token');
      
      console.log('Fetching next question for session:', sessionData.sessionId);

      const response = await axios.post(
        `${API_URL}/api/practice/next-question`,
        { session_id: sessionData.sessionId },
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          timeout: 10000
        }
      );

      console.log('Next question received:', response.data);
      setQuestion(response.data.data.question || 'Tell me about yourself');
      setSessionId(sessionData.sessionId);
      setCurrentQuestion(sessionData.currentQuestion || 1);
      setSessionStarted(true);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch next question:', error.response?.data || error.message);
      setError('Could not load the next question.');
    }
  };

  const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      }
    });

    // Use WebM/Opus codec (what Google Cloud expects)
    const options = {
      mimeType: 'audio/wav',
      audioBitsPerSecond: 48000
    };

    // Fallback if WebM/Opus not supported
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
      console.warn('WebM/Opus not supported, using default');
      mediaRecorderRef.current = new MediaRecorder(stream);
    } else {
      mediaRecorderRef.current = new MediaRecorder(stream, options);
    }

    audioChunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => {
      audioChunksRef.current.push(event.data);
    };

    mediaRecorderRef.current.onstop = () => {
      console.log('Recording stopped, processing audio...');
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
      console.log('Audio blob size:', audioBlob.size, 'bytes');
      analyzeAudio(audioBlob);
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
    setRecordingTime(0);

    timerRef.current = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);

    console.log('Recording started');
  } catch (error) {
    console.error('Microphone error:', error);
    setError('Could not access microphone. Please check browser permissions.');
  }
};

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      
      setIsRecording(false);
      clearInterval(timerRef.current);
      console.log('Recording stopped');
    }
  };

  const analyzeAudio = async (audioBlob) => {
  setIsAnalyzing(true);
  const token = localStorage.getItem('token');

  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('question', question);
    formData.append('session_id', sessionId);

    console.log('Sending audio for analysis:', {
      audioSize: audioBlob.size,
      question: question,
      sessionId: sessionId
    });

    const response = await axios.post(
      `${API_URL}/api/practice/analyze`,
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000  // ← Increased to 2 minutes (was 60s)
      }
    );

    console.log('Analysis response:', response.data);

    navigate('/feedback', {
      state: {
        question: question,
        transcription: response.data.data.transcription || '',
        errors: response.data.data.errors || [],
        sessionId: sessionId,
        currentQuestion: currentQuestion,
        totalQuestions: totalQuestions,
        mode: sessionData.mode,
        role: sessionData.role,
        industry: sessionData.industry
      }
    });
  } catch (error) {
    console.error('Analysis error:', error.response?.data || error.message);
    setError('Could not analyze audio. Please try again.');
    setIsAnalyzing(false);
  }
};

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
        <FiAlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
        <p className="text-gray-600 mb-6 text-center">{error}</p>
        <button 
          onClick={() => navigate('/dashboard')} 
          className="px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-blue-700 transition"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!sessionStarted) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading practice session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header with Progress */}
      <div className="border-b bg-white sticky top-0 z-40 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <span className="text-gray-600 font-medium">
              Question {currentQuestion} of {totalQuestions}
            </span>
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${(currentQuestion / totalQuestions) * 100}%` }}
              ></div>
            </div>
          </div>
          
          <div className="flex gap-3 items-center">
            {isRecording && (
              <div className="flex items-center gap-2 text-red-600">
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
                <span className="text-sm font-semibold">Recording</span>
              </div>
            )}
            <button 
              onClick={() => {
                if (window.confirm('Are you sure you want to end this session?')) {
                  navigate('/dashboard');
                }
              }}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
              title="End session"
            >
              <FiX size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="text-center max-w-2xl w-full">
          {/* Question */}
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-12 leading-tight">
            {question}
          </h2>

          {/* Microphone Button */}
          <div className="flex flex-col items-center">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isAnalyzing}
              className={`w-32 h-32 rounded-full flex items-center justify-center mb-8 transition shadow-lg transform hover:scale-105 active:scale-95 ${
                isRecording
                  ? 'bg-red-500 text-white scale-110'
                  : 'bg-primary text-white hover:bg-blue-700'
              } ${isAnalyzing ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {isAnalyzing ? (
                <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <FiMic size={48} />
              )}
            </button>

            {/* Recording Text */}
            <p className="text-lg text-gray-600 font-medium">
              {isAnalyzing 
                ? 'Analyzing your response...' 
                : isRecording 
                  ? `Recording... ${recordingTime}s` 
                  : 'Click to start speaking'}
            </p>

            {/* Help Text */}
            <p className="text-sm text-gray-500 mt-6 max-w-sm">
              Speak naturally. Your response will be analyzed for pronunciation and grammar. Take your time—there's no time limit.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}