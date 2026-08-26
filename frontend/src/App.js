import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';

// --- PUBLIC PAGE IMPORTS ---
import Landing from './components/pages/Landing';
import About from './components/pages/About';
import Login from './components/pages/Login';
import Register from './components/pages/Register';
import ForgotPassword from './components/pages/ForgotPassword';
import ResetPassword from './components/pages/ResetPassword';

// --- PROTECTED PAGE IMPORTS ---
import Dashboard from './components/pages/Dashboard';
import RoleSelection from './components/pages/RoleSelection';
import PracticeSession from './components/pages/PracticeSession';
import SessionSummary from './components/pages/SessionSummary';
import Profile from './components/pages/Profile';
import Feedback from './components/pages/Feedback';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  // Global State for Authentication
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return !!localStorage.getItem('token');
  });

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch (e) {
        return null;
      }
    }
    return null;
  });

  // Fetch user profile on mount if token exists
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.get(`${API_URL}/api/users/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(res => {
        if (res.data?.data?.user) {
          const userData = res.data.data.user;
          setUser(userData);
          localStorage.setItem('user', JSON.stringify(userData));
        }
      }).catch(err => {
        console.error('Error refreshing profile:', err);
      });
    }
  }, []);

  // --------------------------------------------------------
  // PROTECTED ROUTE COMPONENT
  // If a user tries to access a protected page without being 
  // logged in, this instantly redirects them to the login page.
  // --------------------------------------------------------
  const ProtectedRoute = ({ children }) => {
    if (!isLoggedIn) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };

  return (
    <BrowserRouter>
      <div className="App min-h-screen bg-gray-50 flex flex-col">
        <Routes>
          {/* =========================================
              PUBLIC ROUTES
              Accessible to anyone on the internet.
              ========================================= */}
          <Route path="/" element={<Landing />} />
          <Route path="/about" element={<About />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          
          <Route 
            path="/login" 
            element={<Login setIsLoggedIn={setIsLoggedIn} setUser={setUser} />} 
          />

          {/* =========================================
              ONBOARDING ROUTE (Protected)
              Typically shown right after registration/first login
              ========================================= */}
          <Route 
            path="/role-selection" 
            element={
              <ProtectedRoute>
                <RoleSelection user={user} setUser={setUser} />
              </ProtectedRoute>
            } 
          />

          {/* =========================================
              MAIN APP ROUTES (Protected)
              Requires isLoggedIn = true
              ========================================= */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard user={user} setIsLoggedIn={setIsLoggedIn} />
              </ProtectedRoute>
            } 
          />

          

          {/* =========================================
              PRACTICE & FEEDBACK ROUTES (Protected)
              ========================================= */}
          <Route 
            path="/practice" 
            element={
              <ProtectedRoute>
                <PracticeSession user={user} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/feedback" 
            element={
              <ProtectedRoute>
                <Feedback user={user} />
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/summary" 
            element={
              <ProtectedRoute>
                <SessionSummary user={user} />
              </ProtectedRoute>
            } 
          />

          {/* =========================================
              USER MANAGEMENT ROUTES (Protected)
              ========================================= */}
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <Profile user={user} />
              </ProtectedRoute>
            } 
          />

          
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;