import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiArrowLeft, FiMail } from 'react-icons/fi';
import axios from 'axios';
import logo from '../../assets/logo_icon.png';

const API_URL = (process.env.REACT_APP_API_URL || 'http://localhost:5000').replace(/\/+$/, '');

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setResetToken('');

    if (!email) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/api/auth/forgot-password`, { email });
      const token = res.data?.data?.token;
      
      setSuccess(res.data?.message || 'Password reset link created!');
      if (token) {
        setResetToken(token);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Could not send reset link. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-xl shadow-xl p-8">
        {/* Back Button */}
        <Link 
          to="/login"
          className="flex items-center gap-2 text-gray-600 hover:text-primary mb-8 transition"
        >
          <FiArrowLeft /> Back to login
        </Link>

        {/* Logo */}
        <div className="flex justify-center mb-8">
          <img src={logo} alt="SpeakUp Logo" className="w-16 h-16 object-contain rounded-2xl shadow-md" />
        </div>

        <h2 className="text-3xl font-bold text-gray-900 mb-2 text-center">Forgot Password?</h2>
        <p className="text-gray-600 mb-8 text-center">
          Enter your email and we'll generate a secure link to reset your password.
        </p>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-800 rounded-lg text-sm space-y-3">
            <div className="flex items-start gap-3">
              <FiMail className="mt-0.5 text-green-600 flex-shrink-0 w-5 h-5" />
              <span>{success}</span>
            </div>
            {resetToken && (
              <div className="pt-2 border-t border-green-200">
                <Link
                  to={`/reset-password?token=${resetToken}`}
                  className="block w-full py-2.5 px-4 bg-green-600 hover:bg-green-700 text-white text-center font-semibold rounded-lg shadow transition"
                >
                  👉 Click Here to Reset Password
                </Link>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-primary text-white font-semibold rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed mt-6"
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        {/* Help Text */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-900">
            💡 <strong>Tip:</strong> Check your spam folder if you don't see the email in your inbox.
          </p>
        </div>

        {/* Back to Login */}
        <div className="mt-8 text-center text-sm">
          <span className="text-gray-600">Remember your password? </span>
          <Link to="/login" className="text-primary font-semibold hover:underline">
            Login here
          </Link>
        </div>
      </div>
    </div>
  );
}