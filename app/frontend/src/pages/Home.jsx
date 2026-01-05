import React, { useEffect, useState } from 'react';
import api from '../api';
import { MovieCard } from '../components/MovieCard';
import { MovieModal } from '../components/MovieModal';
import './Pages.css';

import { Search } from 'lucide-react';

const Home = () => {
  const [movies, setMovies] = useState([]);
  const [filteredMovies, setFilteredMovies] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilmId, setSelectedFilmId] = useState(null);

  useEffect(() => {
    const fetchTopMovies = async () => {
      try {
        const response = await api.get('/movies/top');
        const enriched = response.data.map(m => ({
            ...m,
            year: '2023',
            type: 'Movie',
            rank: null,
            description: `A top rated movie with ${m.likes} likes from the community.`
        }));
        setMovies(enriched);
        setFilteredMovies(enriched);
      } catch (err) {
        setError('Failed to load top movies');
      } finally {
        setLoading(false);
      }
    };

    fetchTopMovies();
  }, []);

  const handleSearch = (e) => {
    const term = e.target.value;
    setSearchTerm(term);
    if (!term.trim()) {
      setFilteredMovies(movies);
    } else {
      const filtered = movies.filter(m => 
        m.title.toLowerCase().includes(term.toLowerCase())
      );
      setFilteredMovies(filtered);
    }
  };

  if (loading) return <div className="loading-state">Loading top content...</div>;
  if (error) return <div className="error-state">{error}</div>;

  return (
    <div>
      <section className="hero-section">
        <div className="hero-badge">Social Proof</div>
        <h1 className="page-title">Community Favorites</h1>
        <p className="page-description">
          The most popular films currently trending in our global library. Based on thousands of community interactions.
        </p>
      </section>

      <div className="search-container">
        <div className="search-input-wrapper">
          <Search className="search-icon" size={24} />
          <input
            type="text"
            placeholder="Search through trending titles..."
            value={searchTerm}
            onChange={handleSearch}
            className="search-input"
          />
        </div>
      </div>
      
      <div className="movies-grid">
        {filteredMovies.map((movie, idx) => (
          <MovieCard 
            key={movie.id || idx} 
            movie={movie} 
            onClick={() => movie.id && setSelectedFilmId(movie.id)}
          />
        ))}
      </div>

      {selectedFilmId && (
        <MovieModal 
          filmId={selectedFilmId} 
          onClose={() => setSelectedFilmId(null)} 
        />
      )}
    </div>
  );
};

export default Home;

