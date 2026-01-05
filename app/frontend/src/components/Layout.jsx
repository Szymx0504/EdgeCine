import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Film } from 'lucide-react';
import './Layout.css';

const Layout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <div className="app-container">
      <header className="navbar">
        <div className="container navbar-content">
          <div className="flex-group">
            <Link to="/" className="brand">
              <div className="brand-icon">
                <Film size={20} />
              </div>
              <span>NetRecommender</span>
            </Link>
          </div>
          
          <nav className="nav-links">
             <Link to="/" className={`nav-link ${isActive('/')}`}>Top Movies</Link>
             <Link to="/recommend" className={`nav-link ${isActive('/recommend')}`}>AI Recommend</Link>
             <Link to="/search" className={`nav-link ${isActive('/search')}`}>Search</Link>
          </nav>
          
          <div className="user-section">
            {user ? (
                <>
                    <Link to="/profile" className="welcome-text hidden-mobile">
                        Hello, <strong>{user.name}</strong>
                    </Link>
                    <button className="btn-logout" onClick={logout}>
                      Sign Out
                    </button>
                </>
            ) : (
                <Link to="/login">
                    <button className="btn-login-nav">
                        Sign In
                    </button>
                </Link>
            )}
          </div>
        </div>
      </header>

      <main className="main-content container animate-fade-in">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
