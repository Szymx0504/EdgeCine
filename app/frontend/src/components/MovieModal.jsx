import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Clock, Calendar, MapPin, Star, Users, Tag, Heart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import './MovieModal.css';

export const MovieModal = ({ filmId, onClose, onInteractionChange }) => {
  const { user } = useAuth();
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userLikeId, setUserLikeId] = useState(null);
  const [likeLoading, setLikeLoading] = useState(false);
  const [localLikes, setLocalLikes] = useState(0);
  
  // Star rating state
  const [userRating, setUserRating] = useState(0);
  const [userRatingId, setUserRatingId] = useState(null);
  const [hoverRating, setHoverRating] = useState(0);
  const [ratingLoading, setRatingLoading] = useState(false);

  useEffect(() => {
    const fetchFilm = async () => {
      try {
        const response = await api.get(`/films/${filmId}`);
        setFilm(response.data);
        setLocalLikes(response.data.likes || 0);
      } catch (err) {
        setError('Failed to load film details');
      } finally {
        setLoading(false);
      }
    };

    if (filmId) {
      fetchFilm();
    }
  }, [filmId]);

  // Check if user already liked or rated this film
  useEffect(() => {
    const checkUserInteractions = async () => {
      if (!user || !filmId) return;
      try {
        const response = await api.get(`/users/${user.id}/interactions`);
        const likeInteraction = response.data.find(
          i => i.film_id === filmId && i.interaction_type === 'like'
        );
        if (likeInteraction) {
          setUserLikeId(likeInteraction.id);
        }
        
        // Check for existing rating (rate_1 through rate_5)
        const ratingInteraction = response.data.find(
          i => i.film_id === filmId && i.interaction_type.startsWith('rate_')
        );
        if (ratingInteraction) {
          setUserRatingId(ratingInteraction.id);
          const ratingValue = parseInt(ratingInteraction.interaction_type.split('_')[1]);
          setUserRating(ratingValue);
        }
      } catch (err) {
        console.error('Failed to check user interactions:', err);
      }
    };
    checkUserInteractions();
  }, [user, filmId]);

  const handleLike = async () => {
    if (!user) return;
    setLikeLoading(true);
    try {
      if (userLikeId) {
        await api.delete(`/interactions/${userLikeId}`);
        setUserLikeId(null);
        setLocalLikes(prev => Math.max(0, prev - 1));
      } else {
        const response = await api.post('/interactions', {
          user_id: user.id,
          film_id: filmId,
          interaction_type: 'like'
        });
        setUserLikeId(response.data.id);
        setLocalLikes(prev => prev + 1);
      }
      if (onInteractionChange) onInteractionChange();
    } catch (err) {
      console.error('Failed to toggle like:', err);
    } finally {
      setLikeLoading(false);
    }
  };

  const handleRating = async (rating) => {
    if (!user || ratingLoading) return;
    setRatingLoading(true);
    try {
      // If clicking same rating, remove it
      if (userRating === rating && userRatingId) {
        await api.delete(`/interactions/${userRatingId}`);
        setUserRatingId(null);
        setUserRating(0);
      } else {
        // Delete old rating if exists
        if (userRatingId) {
          await api.delete(`/interactions/${userRatingId}`);
        }
        // Create new rating
        const response = await api.post('/interactions', {
          user_id: user.id,
          film_id: filmId,
          interaction_type: `rate_${rating}`
        });
        setUserRatingId(response.data.id);
        setUserRating(rating);
      }
      if (onInteractionChange) onInteractionChange();
    } catch (err) {
      console.error('Failed to set rating:', err);
    } finally {
      setRatingLoading(false);
    }
  };

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  if (!filmId) return null;

  const modalContent = (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          <X size={24} />
        </button>

        {loading ? (
          <div className="modal-loading">Loading film details...</div>
        ) : error ? (
          <div className="modal-error">{error}</div>
        ) : film ? (
          <>
            <div className="modal-header">
              <span className="modal-type">{film.type}</span>
              <h1 className="modal-title">{film.title}</h1>
              
              <div className="modal-meta">
                {film.release_year && (
                  <span className="meta-item">
                    <Calendar size={16} />
                    {film.release_year}
                  </span>
                )}
                {film.rating && (
                  <span className="meta-item">
                    <Star size={16} />
                    {film.rating}
                  </span>
                )}
                {film.duration_minutes && (
                  <span className="meta-item">
                    <Clock size={16} />
                    {film.duration_minutes} min
                  </span>
                )}
                {film.seasons_count && (
                  <span className="meta-item">
                    <Clock size={16} />
                    {film.seasons_count} season{film.seasons_count > 1 ? 's' : ''}
                  </span>
                )}
                {film.country && (
                  <span className="meta-item">
                    <MapPin size={16} />
                    {film.country}
                  </span>
                )}
                {localLikes > 0 && (
                  <span className="meta-item likes">
                    <Heart size={16} />
                    {localLikes} likes
                  </span>
                )}
                {film.avg_rating && (
                  <span className="meta-item rating">
                    <Star size={16} fill="currentColor" /> {film.avg_rating}
                  </span>
                )}
              </div>
              
              {user && (
                <div className="interaction-buttons">
                  <button 
                    className={`like-button ${userLikeId ? 'liked' : ''}`}
                    onClick={handleLike}
                    disabled={likeLoading}
                  >
                    <Heart size={18} fill={userLikeId ? 'currentColor' : 'none'} />
                    {userLikeId ? 'Liked' : 'Like'}
                  </button>
                  
                  <div className="star-rating">
                    <span className="rating-label">Rate:</span>
                    <div className="stars-container">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          className={`star-btn ${star <= (hoverRating || userRating) ? 'filled' : ''}`}
                          onClick={() => handleRating(star)}
                          onMouseEnter={() => setHoverRating(star)}
                          onMouseLeave={() => setHoverRating(0)}
                          disabled={ratingLoading}
                          title={`Rate ${star} star${star > 1 ? 's' : ''}`}
                        >
                          <Star 
                            size={20} 
                            fill={star <= (hoverRating || userRating) ? 'currentColor' : 'none'} 
                          />
                        </button>
                      ))}
                    </div>
                    {userRating > 0 && (
                      <span className="rating-value">{userRating}/5</span>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="modal-body">
              {film.description && (
                <div className="modal-section">
                  <h3>Description</h3>
                  <p className="modal-description">{film.description}</p>
                </div>
              )}

              {film.director && (
                <div className="modal-section">
                  <h3>Director</h3>
                  <p>{film.director}</p>
                </div>
              )}

              {film.actors && film.actors.length > 0 && (
                <div className="modal-section">
                  <h3><Users size={18} /> Cast</h3>
                  <div className="modal-tags">
                    {film.actors.map((actor, idx) => (
                      <span key={idx} className="actor-tag">{actor}</span>
                    ))}
                  </div>
                </div>
              )}

              {film.tags && film.tags.length > 0 && (
                <div className="modal-section">
                  <h3><Tag size={18} /> Genres</h3>
                  <div className="modal-tags">
                    {film.tags.map((tag, idx) => (
                      <span key={idx} className="genre-tag">{tag}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="modal-extra-info">
                {film.date_added && (
                  <p><strong>Added to library:</strong> {film.date_added}</p>
                )}
                {film.is_short_movie && <p><strong>Short film</strong></p>}
                {film.is_miniseries && <p><strong>Miniseries</strong></p>}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

