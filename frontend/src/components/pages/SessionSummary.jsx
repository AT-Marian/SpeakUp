import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { FiTrendingUp, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

export default function SessionSummary() {
  const location = useLocation();
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    try {
      console.log('=== SessionSummary Component ===');
      console.log('Location state:', location.state);
      
      if (!location.state) {
        console.error('No location state provided');
        setError('Session data not found. Please start a new session.');
        setLoading(false);
        return;
      }

      const summaryData = location.state.summary;
      console.log('Summary data:', summaryData);
      
      if (!summaryData) {
        console.error('No summary in state');
        setError('Summary data is missing');
        setLoading(false);
        return;
      }

      setSummary(summaryData);
      setLoading(false);
      console.log('Summary set successfully');
    } catch (err) {
      console.error('Error processing summary:', err);
      setError(`Error: ${err.message}`);
      setLoading(false);
    }
  }, [location.state]);

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 90) return 'text-green-600';
    if (accuracy >= 80) return 'text-blue-600';
    if (accuracy >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMotivationalMessage = (accuracy) => {
    if (accuracy >= 95) return '🏆 Outstanding performance! You\'re ready for the real thing!';
    if (accuracy >= 85) return '⭐ Great job! Keep practicing to perfection!';
    if (accuracy >= 75) return '💪 Good effort! One more round to really nail it!';
    return '🎯 Keep going! You\'re on the right track!';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading session summary...</p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    console.error('Error state:', error, 'Summary state:', summary);
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
        <FiAlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Unable to Load Summary</h2>
        <p className="text-gray-600 mb-6 text-center">{error || 'Session summary data is missing'}</p>
        <div className="space-y-2">
          <Link 
            to="/dashboard"
            className="inline-block px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Back to Dashboard
          </Link>
          <p className="text-xs text-gray-500">If this persists, try starting a new session</p>
        </div>
      </div>
    );
  }

  // Safely extract summary data with defaults
  const totalQuestions = summary.totalQuestions || 0;
  const grammarErrors = summary.grammarErrors || 0;
  const pronunciationErrors = summary.pronunciationErrors || 0;
  const totalTime = summary.totalTime || '0s';
  const accuracy = summary.accuracy || 0;

  console.log('Rendering with:', { totalQuestions, grammarErrors, pronunciationErrors, totalTime, accuracy });

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
      <div className="max-w-3xl mx-auto px-4">
        {/* Success Icon */}
        <div className="text-center mb-8">
          <div className="inline-block">
            <div className="w-24 h-24 bg-green-500 rounded-full flex items-center justify-center mb-6 shadow-lg">
              <span className="text-5xl">🏆</span>
            </div>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-2 text-center">
          Session Complete!
        </h1>
        <p className="text-gray-600 text-center text-lg mb-12">
          Here's how this session went.
        </p>

        {/* Stats Card */}
        <div className="bg-white rounded-xl shadow-xl p-8 mb-8">
          {/* Main Stats Grid */}
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <p className="text-gray-600 text-sm mb-2 font-semibold uppercase tracking-wide">
                Total Questions
              </p>
              <p className="text-5xl font-bold text-blue-600">{totalQuestions}</p>
            </div>
            
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <p className="text-gray-600 text-sm mb-2 font-semibold uppercase tracking-wide">
                Practice Time
              </p>
              <p className="text-5xl font-bold text-gray-900">{totalTime}</p>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <p className="text-gray-600 text-sm mb-2 font-semibold uppercase tracking-wide">
                Grammar Errors
              </p>
              <p className="text-5xl font-bold text-red-600">{grammarErrors}</p>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <p className="text-gray-600 text-sm mb-2 font-semibold uppercase tracking-wide">
                Pronunciation Errors
              </p>
              <p className="text-5xl font-bold text-blue-600">{pronunciationErrors}</p>
            </div>
          </div>

          {/* Accuracy Circle */}
          <div className="flex justify-center mb-8">
            <div className="relative w-40 h-40">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
                <circle cx="80" cy="80" r="75" fill="none" stroke="#E5E7EB" strokeWidth="8" />
                <circle
                  cx="80"
                  cy="80"
                  r="75"
                  fill="none"
                  stroke="#2563EB"
                  strokeWidth="8"
                  strokeDasharray={`${(accuracy / 100) * 471} 471`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center flex-col">
                <span className={`text-4xl font-bold ${getAccuracyColor(accuracy)}`}>
                  {typeof accuracy === 'number' ? accuracy.toFixed(1) : '0'}%
                </span>
                <span className="text-xs text-gray-600 uppercase tracking-wide">
                  Overall Accuracy
                </span>
              </div>
            </div>
          </div>

          {/* Motivational Message */}
          <div className="text-center p-6 bg-blue-50 rounded-lg border border-blue-200 mb-8">
            <p className="text-lg font-semibold text-gray-900">
              {getMotivationalMessage(accuracy)}
            </p>
          </div>

          {/* Stats Summary */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FiTrendingUp /> Performance Summary
            </h4>
            <ul className="space-y-2 text-gray-700 text-sm">
              <li>✓ You completed <strong>{totalQuestions} practice questions</strong></li>
              <li>✓ You identified <strong>{grammarErrors} grammar issues</strong></li>
              <li>✓ You improved <strong>{pronunciationErrors} pronunciation mistakes</strong></li>
              <li>✓ You spent <strong>{totalTime} in focused practice</strong></li>
              <li>✓ Your overall accuracy was <strong>{typeof accuracy === 'number' ? accuracy.toFixed(1) : '0'}%</strong></li>
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Link 
            to="/role-selection"
            className="flex-1 px-6 py-4 bg-primary text-white rounded-lg font-semibold hover:bg-blue-700 transition text-center"
          >
            Start New Session
          </Link>
          <Link 
            to="/dashboard"
            className="flex-1 px-6 py-4 bg-white text-gray-900 rounded-lg font-semibold hover:bg-gray-50 transition text-center border-2 border-gray-200"
          >
            Back to Dashboard
          </Link>
        </div>

        {/* Next Steps */}
        <div className="mt-12 text-center">
          <h3 className="font-semibold text-gray-900 mb-4">What to do next?</h3>
          <p className="text-gray-600 mb-6 max-w-lg mx-auto">
            Practice makes perfect! Try another session with a different role or industry.
          </p>
        </div>
      </div>
    </div>
  );
}