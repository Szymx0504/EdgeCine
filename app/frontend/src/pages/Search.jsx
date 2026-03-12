import React, { useState } from 'react';
import api from '../api';
import { MovieCard } from '../components/MovieCard';
import { MovieModal } from '../components/MovieModal';
import { Search as SearchIcon } from 'lucide-react';
import './Pages.css';

const Search = () => {
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
      const response = await api.get(`/films/search?query=${encodeURIComponent(query)}`);
      setMovies(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <section className="hero-section">
        <div className="hero-badge">Film Library</div>
        <h1 className="page-title">Search Everything</h1>
        <p className="page-description">
            Quickly find any film in our curated database by searching through titles, cast, or plot descriptions.
        </p>
      </section>

      <div className="search-container">
        <form onSubmit={handleSearch} className="search-input-wrapper">
          <SearchIcon className="search-icon" size={24} />
          <input
            type="text"
            placeholder="Search for movies, actors, or keywords..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="search-input"
          />
        </form>
      </div>

      {loading ? (
        <div className="loading-state">Searching library...</div>
      ) : movies.length > 0 ? (
        <div className="movies-grid">
          {movies.map((movie) => (
             <MovieCard 
               key={movie.id} 
               movie={movie} 
               onClick={() => movie.id && setSelectedFilmId(movie.id)}
             />
          ))}
        </div>
      ) : searched ? (
         <div className="empty-state">No movies found matching your search.</div>
      ) : null}
      
      {selectedFilmId && (
        <MovieModal 
          filmId={selectedFilmId} 
          onClose={() => setSelectedFilmId(null)} 
        />
      )}
    </div>
  );
};

export default Search;
