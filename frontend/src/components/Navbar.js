import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';

const Navbar = ({ user, onLogout }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    setShowUserMenu(false);
    onLogout();
  };

  return (
    <nav className="navbar">
      <Link to="/" className="nav-logo">
        <span className="logo-icon">🤖</span>
        <span>AI Interview Bot</span>
      </Link>
      
      <div className="nav-center">
        <ul className="nav-menu">
          <li>
            <NavLink to="/" className="nav-link" end>Home</NavLink>
          </li>
          <li>
            <NavLink to="/practice" className="nav-link">Practice</NavLink>
          </li>
          <li>
            <NavLink to="/interview" className="nav-link">Interview</NavLink>
          </li>
          <li>
            <NavLink to="/profile" className="nav-link">Profile</NavLink>
          </li>
        </ul>
      </div>

      <div className="nav-user">
        <div 
          className="user-menu-trigger"
          onClick={() => setShowUserMenu(!showUserMenu)}
        >
          <div className="user-avatar">{user?.avatar || '👤'}</div>
          <div className="user-info">
            <span className="user-name">{user?.name || user?.firstName || 'User'}</span>
            <span className="user-role">{user?.profession || 'Member'}</span>
          </div>
          <span className="dropdown-arrow">{showUserMenu ? '▲' : '▼'}</span>
        </div>
        
        {showUserMenu && (
          <div className="user-dropdown">
            <div className="dropdown-header">
              <div className="dropdown-avatar">{user?.avatar || '👤'}</div>
              <div className="dropdown-info">
                <div className="dropdown-name">{user?.name || user?.firstName || 'User'}</div>
                <div className="dropdown-email">{user?.email || 'user@example.com'}</div>
              </div>
            </div>
            <div className="dropdown-divider"></div>
            <Link to="/profile" className="dropdown-item" onClick={() => setShowUserMenu(false)}>
              <span className="item-icon">👤</span>
              <span>My Profile</span>
            </Link>
            <Link to="/interview" className="dropdown-item" onClick={() => setShowUserMenu(false)}>
              <span className="item-icon">🎯</span>
              <span>Start Interview</span>
            </Link>
            <div className="dropdown-divider"></div>
            <button className="dropdown-item logout" onClick={handleLogout}>
              <span className="item-icon">🚪</span>
              <span>Sign Out</span>
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
