import React from 'react';
import './MovieCard.css';

export const MovieCard = ({ movie, onClick }) => {
  return (
    <div className="movie-card" onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <div className="card-content">
        <div className="card-header">
          <span className="movie-type">
            {movie.type}
          </span>
          {movie.rank ? (
            <span className="match-score">
              {(movie.rank * 100).toFixed(0)}% Match
            </span>
          ) : movie.likes ? (
            <span className="match-score like-score">
              ♥ {movie.likes}
            </span>
          ) : null}
        </div>
        
        <h3 className="movie-title">
          {movie.title}
        </h3>
        
        <div className="movie-meta">
             <span>{movie.year}</span>
             {movie.rating && <span>• {movie.rating}</span>}
        </div>

        <p className="movie-description">
          {movie.description}
        </p>
      </div>
    </div>
  );
};

