import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Login.css';

const Login = () => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (isLogin) {
        await login(name, password);
      } else {
        await register(name, password);
        // After register, auto login or ask to login
        await login(name, password);
      }
      navigate('/');
    } catch (err) {
        console.error(err);
      setError(err.response?.data?.detail || 'An error occurred');
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon">N</div>
          <h2 className="login-title">
            {isLogin ? 'Welcome back' : 'Create an account'}
          </h2>
          <p className="login-subtitle">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="link-btn"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>

        <form onSubmit={handleSubmit}>
            <div className="form-group">
                <label className="label">Username</label>
                <input
                    type="text"
                    placeholder="Enter your username"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="input-field"
                />
            </div>
            <div className="form-group">
                <label className="label">Password</label>
                <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="input-field"
                />
            </div>

            {error && (
            <div className="error-message">
                {error}
            </div>
            )}

            <button type="submit" className="btn-submit">
            {isLogin ? 'Sign in' : 'Create account'}
            </button>
        </form>

        <div className="divider">
            <span className="divider-text">Or continue with</span>
        </div>

        <button 
            type="button" 
            className="btn-guest"
            onClick={() => navigate('/')}
        >
            Guest Access
        </button>
      </div>
    </div>
  );
};

export default Login;
