import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// --- PUBLIC PAGE IMPORTS ---
import Landing from './components/pages/Landing';
import About from './components/pages/About';
import Login from './components/pages/Login';
import Register from './components/pages/Register';
import ForgotPassword from './components/pages/ForgotPassword';

// --- PROTECTED PAGE IMPORTS ---
import Dashboard from './components/pages/Dashboard';
import RoleSelection from './components/pages/RoleSelection';
import PracticeSession from './components/pages/PracticeSession';
import SessionSummary from './components/pages/SessionSummary';
import Profile from './components/pages/Profile';
import Feedback from './components/pages/Feedback';


function App() {
  // Global State for Authentication
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);

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