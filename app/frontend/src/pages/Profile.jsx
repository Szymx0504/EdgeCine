import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { MovieModal } from '../components/MovieModal';
import api from '../api';
import './Profile.css';

import { User, Edit2, Trash2, Heart, Eye, Clock, Film, X, Check, Star } from 'lucide-react';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [interactions, setInteractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [isEditing, setIsEditing] = useState(false);
  const [newName, setNewName] = useState(user?.name || '');
  const [updateError, setUpdateError] = useState('');
  
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedFilmId, setSelectedFilmId] = useState(null);


  const fetchInteractions = async () => {
    if (!user) return;
    try {
      const response = await api.get(`/users/${user.id}/interactions`);
      setInteractions(response.data);
    } catch (err) {
      setError('Failed to load interaction history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    
    fetchInteractions();
  }, [user, navigate]);

  const handleUpdateName = async () => {
    if (!newName.trim() || newName === user.name) {
      setIsEditing(false);
      return;
    }
    
    try {
      await api.put(`/users/${user.id}`, { name: newName });
      // Update local storage
      const updatedUser = { ...user, name: newName };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      window.location.reload(); // Simple refresh to update context
    } catch (err) {
      setUpdateError(err.response?.data?.detail || 'Failed to update username');
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await api.delete(`/users/${user.id}`);
      logout();
      navigate('/login');
    } catch (err) {
      setUpdateError(err.response?.data?.detail || 'Failed to delete account');
    }
  };

  const handleDeleteInteraction = async (interactionId) => {
    try {
      await api.delete(`/interactions/${interactionId}`);
      setInteractions(prev => prev.filter(i => i.id !== interactionId));
    } catch (err) {
      console.error('Failed to delete interaction:', err);
    }
  };

  const getInteractionIcon = (type) => {
    if (type === 'like') return <Heart size={16} className="icon-like" />;
    if (type === 'view') return <Eye size={16} className="icon-view" />;
    if (type.startsWith('rate_')) return <Star size={16} className="icon-rating" />;
    return <Film size={16} />;
  };

  const formatInteractionType = (type) => {
    if (type.startsWith('rate_')) {
      const rating = type.split('_')[1];
      return `Rated ${rating}/5`;
    }
    return type;
  };

  if (!user) return null;

  return (
    <div className="profile-page">
      <section className="profile-header">
        <div className="profile-avatar">
          <User size={48} />
        </div>
        
        <div className="profile-info">
          {isEditing ? (
            <div className="edit-name-form">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="edit-name-input"
                autoFocus
              />
              <button onClick={handleUpdateName} className="btn-icon btn-confirm">
                <Check size={18} />
              </button>
              <button onClick={() => { setIsEditing(false); setNewName(user.name); }} className="btn-icon btn-cancel">
                <X size={18} />
              </button>
            </div>
          ) : (
            <div className="name-display">
              <h1 className="profile-name">{user.name}</h1>
              <button onClick={() => setIsEditing(true)} className="btn-icon btn-edit">
                <Edit2 size={18} />
              </button>
            </div>
          )}
          
          <p className="profile-id">User ID: {user.id}</p>
          
          {updateError && <p className="error-text">{updateError}</p>}
        </div>
        
        <div className="profile-actions">
          {showDeleteConfirm ? (
            <div className="delete-confirm">
              <span>Are you sure?</span>
              <button onClick={handleDeleteAccount} className="btn-danger">Yes, Delete</button>
              <button onClick={() => setShowDeleteConfirm(false)} className="btn-secondary">Cancel</button>
            </div>
          ) : (
            <button onClick={() => setShowDeleteConfirm(true)} className="btn-danger-outline">
              <Trash2 size={16} /> Delete Account
            </button>
          )}
        </div>
      </section>

      <section className="history-section">
        <h2 className="section-title">
          <Clock size={24} /> Interaction History
        </h2>
        <p className="section-description">Your activity with films in our library</p>
        
        {loading ? (
          <div className="loading-state">Loading history...</div>
        ) : error ? (
          <div className="error-state">{error}</div>
        ) : interactions.length === 0 ? (
          <div className="empty-state">
            <Film size={48} />
            <p>No interactions yet. Start exploring films!</p>
          </div>
        ) : (
          <div className="history-list">
            {interactions.map((interaction) => (
              <div key={interaction.id} className="history-item">
                <div className="history-icon">
                  {getInteractionIcon(interaction.interaction_type)}
                </div>
                <div 
                  className="history-content"
                  onClick={() => setSelectedFilmId(interaction.film_id)}
                >
                  <span className="history-title">{interaction.title}</span>
                  <span className="history-type">{interaction.film_type}</span>
                </div>
                <div className="history-meta">
                  <span className="history-action">{formatInteractionType(interaction.interaction_type)}</span>
                  <span className="history-time">
                    {new Date(interaction.interaction_timestamp).toLocaleDateString()}
                  </span>
                </div>
                <button 
                  onClick={() => handleDeleteInteraction(interaction.id)}
                  className="btn-icon btn-remove"
                  title="Remove interaction"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {selectedFilmId && (
        <MovieModal 
          filmId={selectedFilmId} 
          onClose={() => setSelectedFilmId(null)}
          onInteractionChange={fetchInteractions}
        />
      )}
    </div>
  );
};

export default Profile;
