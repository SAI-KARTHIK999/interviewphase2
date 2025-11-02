import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Interview from './pages/Interview';
import Practice from './pages/Practice';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Signup from './pages/Signup';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing authentication on app load
  useEffect(() => {
    const checkAuth = () => {
      try {
        const savedUser = localStorage.getItem('user');
        const authStatus = localStorage.getItem('isAuthenticated');
        
        if (savedUser && authStatus === 'true') {
          setUser(JSON.parse(savedUser));
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Error loading user data:', error);
        // Clear corrupted data
        localStorage.removeItem('user');
        localStorage.removeItem('isAuthenticated');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('isAuthenticated');
    setUser(null);
    setIsAuthenticated(false);
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading AI Interview Bot...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="app-container">
        {isAuthenticated && <Navbar user={user} onLogout={handleLogout} />}
        <main className={`main-content ${!isAuthenticated ? 'auth-main' : ''}`}>
          <Routes>
            {/* Protected Routes */}
            {isAuthenticated ? (
              <>
                <Route path="/" element={<Home user={user} />} />
                <Route path="/interview" element={<Interview user={user} />} />
                <Route path="/practice" element={<Practice user={user} />} />
                <Route path="/profile" element={<Profile user={user} />} />
                <Route path="/login" element={<Navigate to="/" replace />} />
                <Route path="/signup" element={<Navigate to="/" replace />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </>
            ) : (
              <>
                {/* Public Routes */}
                <Route path="/login" element={<Login onLogin={handleLogin} />} />
                <Route path="/signup" element={<Signup onLogin={handleLogin} />} />
                <Route path="*" element={<Navigate to="/login" replace />} />
              </>
            )}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
