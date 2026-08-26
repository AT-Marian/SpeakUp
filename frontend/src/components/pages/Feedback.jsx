import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FiCheckCircle, FiArrowRight, FiAlertCircle } from 'react-icons/fi';
import axios from 'axios';

const API_URL = (process.env.REACT_APP_API_URL || 'http://localhost:5000').replace(/\/+$/, '');

export default function Feedback() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isRerecording, setIsRerecording] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);
  
  const stateData = location.state;

  // Log for debugging
  console.log('=== FEEDBACK PAGE ===');
  console.log('State Data:', stateData);

  if (!stateData) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
        <FiAlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">No feedback data found</h2>
        <p className="text-gray-600 mb-6">You may have refreshed the page. Please complete a practice session to see feedback.</p>
        <button 
          onClick={() => navigate('/dashboard')} 
          className="px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-blue-700 transition"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const { 
    question = 'Question not available',  // ← ADD DEFAULT VALUE
    transcription = '', 
    errors = [], 
    sessionId,
    currentQuestion = 1, 
    totalQuestions = 5,
    mode,
    role,
    industry
  } = stateData;

  console.log('Question:', question);
  console.log('Transcription:', transcription);
  console.log('Errors:', errors);

  const hasErrors = errors && errors.length > 0;
  const isTranscriptionEmpty = !transcription || transcription.trim() === '';
  const isLastQuestion = currentQuestion >= totalQuestions;

  const handleRerecord = () => {
    setIsRerecording(true);
    setTimeout(() => {
      navigate('/practice', { 
        state: { 
          sessionId,
          isRerecord: true, 
          question: question,  // ← PASS QUESTION BACK
          currentQuestion,
          totalQuestions,
          mode,
          role,
          industry
        } 
      });
    }, 500);
  };

  const handleNextQuestion = () => {
    navigate('/practice', {
      state: { 
        sessionId,
        isNextQuestion: true, 
        currentQuestion: currentQuestion + 1,
        totalQuestions,
        mode,
        role,
        industry
      }
    });
  };

  const handleFinishSession = async () => {
  console.log('\n=== FINISHING SESSION ===');
  console.log('Session ID:', sessionId);
  console.log('Current Question:', currentQuestion);
  console.log('Total Questions:', totalQuestions);
  
  setIsFinishing(true);
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      console.error('No token found');
      alert('You are not logged in. Please login and try again.');
      navigate('/login');
      return;
    }

    if (!sessionId) {
      console.error('No session ID');
      alert('Session ID is missing');
      return;
    }
    
    console.log('[→] Sending finish session request...');

    const response = await axios.post(
      `${API_URL}/api/practice/finish`, 
      { session_id: sessionId },
      { 
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000
      }
    );

    console.log('[✓] Finish session response status:', response.status);
    console.log('[✓] Response data:', response.data);

    if (!response.data || !response.data.data || !response.data.data.summary) {
      console.error('Invalid response structure:', response.data);
      alert('Invalid response from server');
      return;
    }

    const summary = response.data.data.summary;
    console.log('[✓] Summary extracted:', summary);

    console.log('[→] Navigating to session summary...');
    navigate('/summary', {
      state: {
        summary: summary,
        sessionId: sessionId
      }
    });
    
    console.log('[✓] Navigation called');

  } catch (error) {
    console.error('\n=== ERROR IN handleFinishSession ===');
    console.error('Error message:', error.message);
    console.error('Response status:', error.response?.status);
    console.error('Response data:', error.response?.data);
    console.error('Full error:', error);
    
    alert(`Error: ${error.response?.data?.message || error.message}`);
    setIsFinishing(false);
  }
};

  const renderTranscription = () => {
    if (isTranscriptionEmpty) {
      return (
        <span className="text-gray-500 italic">
          No speech was detected. Please make sure your microphone is working and speak clearly.
        </span>
      );
    }

    let words = transcription.split(' ');
    
    return words.map((word, index) => {
      const wordError = errors?.find(e => e.position === index + 1);
      
      if (!wordError) {
        return <span key={index}>{word} </span>;
      }

      const bgColor = wordError.type === 'grammar' ? 'bg-red-200 text-red-900' : 'bg-blue-200 text-blue-900';
      return (
        <span key={index} className={`${bgColor} px-2 py-1 rounded font-semibold`}>
          {word}{' '}
        </span>
      );
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-12">
      <div className="max-w-3xl mx-auto px-4">
        {/* Progress */}
        <p className="text-gray-600 text-sm mb-8 opacity-75">
          Question {currentQuestion} of {totalQuestions}
        </p>

        {/* QUESTION DISPLAY - ALWAYS SHOW THIS */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-300 rounded-xl p-8 mb-8">
          <p className="text-gray-600 text-sm font-semibold uppercase tracking-wide mb-3">
            Question Asked:
          </p>
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900">
            "{question}"
          </h2>
        </div>

        {/* Transcription Box */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h3 className="font-semibold text-gray-900 mb-4 text-lg">Your Response:</h3>
          <div className="text-xl text-gray-900 leading-relaxed mb-6 min-h-24 p-4 bg-gray-50 rounded-lg">
            {renderTranscription()}
          </div>
        </div>

        {/* Errors Section */}
        {!isTranscriptionEmpty && hasErrors ? (
          <div className="space-y-4 mb-8">
            <h3 className="font-semibold text-gray-900 text-lg">
              Corrections needed ({errors.length}):
            </h3>
            {errors.map((error, idx) => (
              <div key={idx} className={`border-l-4 p-4 rounded-r-lg ${
                error.type === 'grammar' 
                  ? 'border-red-400 bg-red-50' 
                  : 'border-blue-400 bg-blue-50'
              }`}>
                <div className="flex items-center gap-3 mb-2 flex-wrap">
                  <span className="font-semibold text-gray-900">
                    "{error.word}"
                  </span>
                  <FiArrowRight className="text-gray-500" />
                  <span className="font-semibold text-gray-900">
                    "{error.correction}"
                  </span>
                </div>
                <p className={`text-sm ${
                  error.type === 'grammar' 
                    ? 'text-red-700' 
                    : 'text-blue-700'
                }`}>
                  <strong>{error.type === 'grammar' ? '✓ Grammar:' : '🔊 Pronunciation:'}</strong> {error.explanation}
                </p>
              </div>
            ))}
          </div>
        ) : !isTranscriptionEmpty && !hasErrors ? (
          <div className="bg-white rounded-xl shadow-lg p-12 mb-8 text-center border-2 border-green-200">
            <FiCheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Perfect! No errors detected.</h3>
            <p className="text-gray-600">Excellent pronunciation and grammar!</p>
          </div>
        ) : null}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <button 
            onClick={handleRerecord}
            disabled={isRerecording}
            className="flex-1 px-6 py-4 bg-primary text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
          >
            🎤 {isRerecording ? 'Starting...' : 'Re-record'}
          </button>
          
          {isLastQuestion ? (
            <button 
              onClick={handleFinishSession}
              disabled={isFinishing}
              className="flex-1 px-6 py-4 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
            >
              {isFinishing ? 'Finishing...' : 'Finish Session'} <FiCheckCircle />
            </button>
          ) : (
            <button 
              onClick={handleNextQuestion}
              className="flex-1 px-6 py-4 bg-gray-200 text-gray-900 rounded-lg font-semibold hover:bg-gray-300 transition flex items-center justify-center gap-2"
            >
              Next Question <FiArrowRight />
            </button>
          )}
        </div>

        {/* Tips Section */}
        <div className="mt-12 bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h4 className="font-semibold text-gray-900 mb-2">💡 Tip:</h4>
          <p className="text-gray-600 text-sm">
            Try re-recording the same question until you get it perfect. The more you practice, the better you'll get!
          </p>
        </div>
      </div>
    </div>
  );
}