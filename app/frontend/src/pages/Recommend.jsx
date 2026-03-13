import React, { useState } from 'react';
import api from '../api';
import { MovieCard } from '../components/MovieCard';
import { MovieModal } from '../components/MovieModal';
import { Search, Sparkles } from 'lucide-react';
import './Recommend.css';

const Recommend = () => {
  const [query, setQuery] = useState('');
  const [movies, setMovies] = useState([]);
  const [insight, setInsight] = useState('');
  const [insightHeader, setInsightHeader] = useState('');
  const [displayInsight, setDisplayInsight] = useState('');
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selectedFilmId, setSelectedFilmId] = useState(null);
  const [telemetry, setTelemetry] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setMovies([]);
    setInsight('');
    setInsightHeader('');
    setDisplayInsight('');
    
    try {
      const response = await api.get(`/films/recommend?q=${encodeURIComponent(query)}`);
      const { results, neural_insight, neural_insight_header, telemetry } = response.data;
      
      setMovies(results);
      setTelemetry(telemetry);
      setInsight(neural_insight);
      setInsightHeader(neural_insight_header || "Neural Insight");
      
      // Basic typewriter effect
      let current = '';
      const words = neural_insight.split(' ');
      for (let i = 0; i < words.length; i++) {
        await new Promise(r => setTimeout(r, 40));
        current += (i === 0 ? '' : ' ') + words[i];
        setDisplayInsight(current);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="recommend-container animate-fade-in">
      <section className="recommend-hero">
        <div className="hero-content">
          <div className="ai-badge">
            <Sparkles size={14} />
            <span>AI Discovery Engine</span>
          </div>
          <h1 className="recommend-title">Personal AI Assistant</h1>
          <p className="recommend-description">
            Describe your perfect movie in natural language. Our neural engine will analyze your request and find the most relevant titles in our library.
          </p>
        </div>
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
          <div className="neural-wave">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
          <div className="loading-text">Our AI is scanning the library for you...</div>
        </div>
      ) : searched ? (
        <>
          {displayInsight && (
            <div className="insight-box glass-effect animate-slide-up">
              <div className="insight-header">
                <Sparkles size={18} className="text-accent" />
                <h3>{insightHeader}</h3>
              </div>
              <p className="insight-text">{displayInsight}</p>
              
              {telemetry && (
                <div className="neural-monitor animate-fade-in">
                  <div className="monitor-item">
                    <span className="monitor-label">Latency:</span>
                    <span className="monitor-value">{telemetry.inference_time_ms}ms</span>
                  </div>
                  <div className="monitor-item">
                    <span className="monitor-label">Variant:</span>
                    <span className="monitor-value">{telemetry.model_variant}</span>
                  </div>
                  <div className="monitor-item">
                    <span className="monitor-label">Engine:</span>
                    <span className="monitor-value">{telemetry.vector_engine}</span>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {movies.length > 0 ? (
            <div className="recommend-grid">
              {movies.map((movie) => (
                 <MovieCard 
                   key={movie.id || movie.title} 
                   movie={movie} 
                   onClick={() => movie.id && setSelectedFilmId(movie.id)}
                 />
              ))}
            </div>
          ) : (
            <div className="recommend-empty">
               <h3>No matches found</h3>
               <p>Try refining your description or using different keywords.</p>
            </div>
          )}
        </>
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
