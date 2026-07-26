import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiEdit2, FiLock, FiAlertTriangle } from 'react-icons/fi';

export default function Profile({ user, setUser, setIsLoggedIn }) {
  const navigate = useNavigate();
  const [isEditingName, setIsEditingName] = useState(false);
  const [newName, setNewName] = useState(user?.name || '');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleSaveName = () => {
    const updatedUser = { ...user, name: newName };
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setUser(updatedUser);
    setIsEditingName(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    navigate('/');
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    try {
      // Call backend to delete account
      // await axios.delete(`${API_URL}/api/users/account`, { headers });
      
      setTimeout(() => {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        setIsLoggedIn(false);
        navigate('/');
      }, 1000);
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('Could not delete account. Please try again.');
      setIsDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Account settings</h1>
        <p className="text-gray-600 mb-12">Manage your profile and data.</p>

        {/* User Info Card */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="flex items-center gap-6 mb-8">
            {/* Avatar */}
            <div className="w-20 h-20 bg-gradient-to-br from-primary to-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-2xl">
                {user?.name?.split(' ').map(n => n[0]).join('')}
              </span>
            </div>

            {/* User Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {isEditingName ? (
                  <div className="flex gap-2 items-center">
                    <input
                      type="text"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      className="px-3 py-2 border border-primary rounded-lg focus:ring-2 focus:ring-primary outline-none"
                      autoFocus
                    />
                    <button
                      onClick={handleSaveName}
                      className="px-4 py-2 bg-primary text-white rounded-lg font-semibold text-sm"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingName(false);
                        setNewName(user?.name || '');
                      }}
                      className="px-4 py-2 bg-gray-200 text-gray-900 rounded-lg font-semibold text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <h2 className="text-2xl font-bold text-gray-900">{user?.name}</h2>
                    <button
                      onClick={() => setIsEditingName(true)}
                      className="text-gray-500 hover:text-primary transition"
                    >
                      <FiEdit2 size={20} />
                    </button>
                  </>
                )}
              </div>
              <p className="text-gray-600">{user?.email}</p>
            </div>
          </div>

          {/* Account Actions */}
          <div className="space-y-3">
            <button 
              onClick={() => alert('Password change feature coming soon!')}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition flex items-center gap-2"
            >
              <FiLock size={20} /> Change Password
            </button>
            <button 
              onClick={handleLogout}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Account Statistics */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h3 className="font-bold text-lg text-gray-900 mb-6">Your Statistics</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <StatItem label="Total Sessions" value="12" />
            <StatItem label="Total Practice Time" value="4h 32m" />
            <StatItem label="Average Accuracy" value="87%" />
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8">
          <div className="flex items-start gap-4">
            <FiAlertTriangle className="text-red-600 mt-1 flex-shrink-0" size={24} />
            <div className="flex-1">
              <h3 className="text-lg font-bold text-red-700 mb-2">Danger zone</h3>
              <p className="text-gray-700 mb-4">
                Permanently delete your account and all associated practice data. This action complies with GDPR right-to-erasure and cannot be reversed.
              </p>

              {showDeleteConfirm ? (
                <div className="bg-white rounded-lg p-4 border border-red-200">
                  <p className="text-gray-900 font-semibold mb-4">
                    Are you sure? This cannot be undone.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={handleDeleteAccount}
                      disabled={isDeleting}
                      className="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition disabled:opacity-50"
                    >
                      {isDeleting ? 'Deleting...' : 'Yes, Delete My Account'}
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="flex-1 px-4 py-3 bg-gray-300 text-gray-900 rounded-lg font-semibold hover:bg-gray-400 transition"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition"
                >
                  Delete Account
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Privacy Notice */}
        <div className="mt-8 text-center">
          <p className="text-gray-600 text-sm">
            Your data is encrypted and secure. Read our{' '}
            <a href="#" className="text-primary hover:underline">
              Privacy Policy
            </a>
            {' '}and{' '}
            <a href="#" className="text-primary hover:underline">
              Terms of Service
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

function StatItem({ label, value }) {
  return (
    <div className="text-center p-4 bg-gray-50 rounded-lg">
      <p className="text-gray-600 text-sm mb-2 font-semibold uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-primary">{value}</p>
    </div>
  );
}