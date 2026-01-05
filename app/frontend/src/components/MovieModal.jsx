import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Clock, Calendar, MapPin, Star, Users, Tag, Heart } from 'lucide-react';
import api from '../api';
import './MovieModal.css';

export const MovieModal = ({ filmId, onClose }) => {
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFilm = async () => {
      try {
        const response = await api.get(`/films/${filmId}`);
        setFilm(response.data);
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
                {film.likes > 0 && (
                  <span className="meta-item likes">
                    <Heart size={16} />
                    {film.likes} likes
                  </span>
                )}
              </div>
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

