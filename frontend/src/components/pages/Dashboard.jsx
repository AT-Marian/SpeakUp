import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiTarget, FiClock, FiTrendingUp, FiActivity } from 'react-icons/fi';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Dashboard({ user }) {
  const [stats, setStats] = useState({
    sessionsThisWeek: 0,
    practiceTime: '0h 0m',
    avgAccuracy: 0,
    recentSessions: [] // Added this to catch the new backend data
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const getFirstName = () => {
    let u = user;
    if (!u) {
      try {
        u = JSON.parse(localStorage.getItem('user'));
      } catch (e) {
        u = null;
      }
    }
    if (u?.name) {
      return u.name.trim().split(' ')[0];
    }
    if (u?.email) {
      const namePart = u.email.split('@')[0];
      return namePart.charAt(0).toUpperCase() + namePart.slice(1);
    }
    return '';
  };

  const firstName = getFirstName();

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/users/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Welcome Section */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Welcome back{firstName ? `, ${firstName}` : ''}!
          </h1>
          <p className="text-gray-600">Pick up where you left off, or start fresh.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <StatCard 
            icon={<FiTarget className="w-6 h-6" />}
            title="Sessions this week"
            value={stats.sessionsThisWeek}
          />
          <StatCard 
            icon={<FiClock className="w-6 h-6" />}
            title="Practice time"
            value={stats.practiceTime}
          />
          <StatCard 
            icon={<FiTrendingUp className="w-6 h-6" />}
            title="Avg. accuracy"
            value={`${stats.avgAccuracy}%`}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          
          {/* Practice Modes (Takes up 2/3 of the screen) */}
          <div className="lg:col-span-2">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Choose your practice mode</h2>
            <div className="grid sm:grid-cols-2 gap-6">
              <Link to="/role-selection" state={{ mode: 'interview' }}>
                <div className="p-8 bg-white border-2 border-gray-200 rounded-xl hover:shadow-xl hover:border-primary transition cursor-pointer h-full flex flex-col">
                  <div className="text-5xl mb-4">🎯</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Interview Practice</h3>
                  <p className="text-gray-600 mb-6 flex-1">
                    Practice answering common, industry-specific job interview questions.
                  </p>
                  <span className="text-primary font-semibold inline-flex items-center gap-2 mt-auto">
                    Start session <span>→</span>
                  </span>
                </div>
              </Link>

              <Link to="/role-selection" state={{ mode: 'meeting' }}>
                <div className="p-8 bg-white border-2 border-gray-200 rounded-xl hover:shadow-xl hover:border-primary transition cursor-pointer h-full flex flex-col">
                  <div className="text-5xl mb-4">💼</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Client Meeting</h3>
                  <p className="text-gray-600 mb-6 flex-1">
                    Practice professional business conversations and presentation scenarios.
                  </p>
                  <span className="text-primary font-semibold inline-flex items-center gap-2 mt-auto">
                    Start session <span>→</span>
                  </span>
                </div>
              </Link>
            </div>
          </div>

          {/* Recent History Sidebar (Takes up 1/3 of the screen) */}
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <FiActivity /> Recent History
            </h2>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {stats.recentSessions && stats.recentSessions.length > 0 ? (
                <div className="divide-y divide-gray-100">
                  {stats.recentSessions.map((session, idx) => (
                    <div key={idx} className="p-4 hover:bg-gray-50 transition">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-semibold text-gray-900">{session.role}</span>
                        <span className={`text-sm font-bold ${
                          session.accuracy >= 90 ? 'text-green-600' : 
                          session.accuracy >= 75 ? 'text-blue-600' : 'text-yellow-600'
                        }`}>
                          {session.accuracy}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm text-gray-500">
                        <span>{session.mode}</span>
                        <span>{session.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  <p className="mb-2">No sessions yet!</p>
                  <p className="text-sm">Your recent practice history will appear here.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, title, value }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-primary hover:shadow-md transition">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm mb-1 font-medium">{title}</p>
          <p className="text-4xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="text-primary opacity-30 text-3xl bg-blue-50 p-3 rounded-full">
          {icon}
        </div>
      </div>
    </div>
  );
}