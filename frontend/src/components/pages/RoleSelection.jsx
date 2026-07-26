import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowLeft } from 'react-icons/fi';

export default function RoleSelection() {
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [selectedMode, setSelectedMode] = useState('interview');  // ← ADD MODE STATE
  const navigate = useNavigate();

  const roles = [
    'Software Engineer', 'Marketing Manager', 'Sales Executive',
    'Teacher', 'Healthcare Professional', 'Business Analyst',
    'Project Manager', 'Customer Service Rep', 'Financial Analyst', 'HR Manager'
  ];

  const industries = [
    'Technology', 'Healthcare', 'Finance', 'Education', 'Retail',
    'Manufacturing', 'Hospitality', 'Legal', 'Engineering', 'Marketing'
  ];

  const handleStart = () => {
    if (!selectedRole || !selectedIndustry) {
      alert('Please select both role and industry');
      return;
    }
    
    console.log('Starting session with:', { 
      role: selectedRole, 
      industry: selectedIndustry, 
      mode: selectedMode 
    });

    navigate('/practice', { 
      state: { 
        role: selectedRole, 
        industry: selectedIndustry, 
        mode: selectedMode,  // ← PASS MODE
        currentQuestion: 1,
        totalQuestions: 5
      } 
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <button 
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-gray-600 hover:text-primary mb-8 transition"
        >
          <FiArrowLeft /> Back to dashboard
        </button>

        <h1 className="text-4xl font-bold text-gray-900 mb-2">Set up your practice session</h1>
        <p className="text-gray-600 mb-8">We'll tailor questions to your role and industry.</p>

        <div className="bg-white rounded-xl shadow-lg p-8 space-y-6">
          {/* Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3 font-semibold">
              Select Practice Mode
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setSelectedMode('interview')}
                className={`p-4 rounded-lg border-2 transition font-semibold ${
                  selectedMode === 'interview'
                    ? 'border-primary bg-blue-50 text-primary'
                    : 'border-gray-300 text-gray-600 hover:border-primary'
                }`}
              >
                🎤 Interview
              </button>
              <button
                onClick={() => setSelectedMode('meeting')}
                className={`p-4 rounded-lg border-2 transition font-semibold ${
                  selectedMode === 'meeting'
                    ? 'border-primary bg-blue-50 text-primary'
                    : 'border-gray-300 text-gray-600 hover:border-primary'
                }`}
              >
                💼 Client Meeting
              </button>
            </div>
          </div>

          {/* Role Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3 font-semibold">
              Select Your Role
            </label>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
            >
              <option value="">Choose...</option>
              {roles.map(role => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </div>

          {/* Industry Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3 font-semibold">
              Select Your Industry
            </label>
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
            >
              <option value="">Choose...</option>
              {industries.map(industry => (
                <option key={industry} value={industry}>{industry}</option>
              ))}
            </select>
          </div>

          {/* Start Button */}
          <button
            onClick={handleStart}
            disabled={!selectedRole || !selectedIndustry}
            className={`w-full py-3 rounded-lg font-semibold transition ${
              selectedRole && selectedIndustry
                ? 'bg-primary text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            Start Practice
          </button>

          {!selectedRole || !selectedIndustry ? (
            <p className="text-center text-gray-500 text-sm">Both selections are required.</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}