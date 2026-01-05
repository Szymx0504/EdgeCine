import React, { useState } from 'react';
import api from '../api';
import { MovieCard } from '../components/MovieCard';
import { MovieModal } from '../components/MovieModal';
import { Search, Sparkles } from 'lucide-react';
import './Recommend.css';

const Recommend = () => {
  const [query, setQuery] = useState('');
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selectedFilmId, setSelectedFilmId] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const response = await api.get(`/films/recommend?q=${encodeURIComponent(query)}`);
      setMovies(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="recommend-container animate-fade-in">
      <section className="recommend-hero">
        <div className="ai-badge">
          <Sparkles size={14} />
          <span>AI Discovery Engine</span>
        </div>
        <h1 className="recommend-title">Personal AI Assistant</h1>
        <p className="recommend-description">
          Describe your perfect movie in natural language. Our neural engine will analyze your request and find the most relevant titles in our library.
        </p>
      </section>

      <div className="recommend-search-wrapper">
        <form onSubmit={handleSearch} className="recommend-search-form">
          <Search className="search-input-icon" size={22} />
          <input
            type="text"
            placeholder="e.g. A mind-bending thriller with a twist ending like Inception..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="recommend-input"
          />
          <button type="submit" className="recommend-submit">
            Search
          </button>
        </form>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <div className="loading-text">Our AI is scanning the library for you...</div>
        </div>
      ) : movies.length > 0 ? (
        <div className="recommend-grid">
          {movies.map((movie) => (
             <MovieCard 
               key={movie.id || movie.title} 
               movie={movie} 
               onClick={() => movie.id && setSelectedFilmId(movie.id)}
             />
          ))}
        </div>
      ) : searched ? (
        <div className="recommend-empty">
           <h3>No matches found</h3>
           <p>Try refining your description or using different keywords.</p>
        </div>
      ) : (
        <div className="recommend-empty">
          <p>Ready to find your next favorite movie?</p>
        </div>
      )}

      {selectedFilmId && (
        <MovieModal 
          filmId={selectedFilmId} 
          onClose={() => setSelectedFilmId(null)} 
        />
      )}
    </div>
  );
};

export default Recommend;
