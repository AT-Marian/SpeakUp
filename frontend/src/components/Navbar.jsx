import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FiMenu, FiX, FiLogOut, FiUser } from 'react-icons/fi';
import logo from '../assets/logo_icon.png';

export default function Navbar({ isLoggedIn, user, setIsLoggedIn }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    navigate('/');
  };

  const getFirstName = () => {
    let u = user;
    if (!u) {
      try {
        u = JSON.parse(localStorage.getItem('user'));
      } catch (e) {
        u = null;
      }
    }
    if (u?.name) return u.name.trim().split(' ')[0];
    if (u?.email) return u.email.split('@')[0];
    return 'Profile';
  };

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <img src={logo} alt="SpeakUp Logo" className="w-10 h-10 object-contain rounded-lg shadow-sm" />
            <span className="text-xl font-bold text-gray-900 hidden sm:inline">SpeakUp</span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex gap-8 items-center">
            {!isLoggedIn ? (
              <>
                <Link to="/" className="text-gray-600 hover:text-primary transition">
                  Home
                </Link>
                <Link to="/about" className="text-gray-600 hover:text-primary transition">
                  Features
                </Link>
                <Link to="/login" className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 transition">
                  Login
                </Link>
              </>
            ) : (
              <>
                <Link to="/dashboard" className="text-gray-600 hover:text-primary transition">
                  Dashboard
                </Link>
                <Link to="/profile" className="flex items-center gap-2 text-gray-600 hover:text-primary transition">
                  <FiUser /> {getFirstName()}
                </Link>
                <button 
                  onClick={handleLogout} 
                  className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                >
                  <FiLogOut /> Logout
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <div className="md:hidden pb-4 space-y-2 border-t">
            {!isLoggedIn ? (
              <>
                <Link to="/" className="block px-4 py-2 text-gray-600 hover:bg-gray-100">
                  Home
                </Link>
                <Link to="/about" className="block px-4 py-2 text-gray-600 hover:bg-gray-100">
                  Features
                </Link>
                <Link to="/login" className="block px-4 py-2 text-primary font-bold bg-blue-50">
                  Login
                </Link>
              </>
            ) : (
              <>
                <Link to="/dashboard" className="block px-4 py-2 text-gray-600 hover:bg-gray-100">
                  Dashboard
                </Link>
                <Link to="/profile" className="block px-4 py-2 text-gray-600 hover:bg-gray-100">
                  Profile
                </Link>
                <button 
                  onClick={handleLogout} 
                  className="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50"
                >
                  Logout
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}