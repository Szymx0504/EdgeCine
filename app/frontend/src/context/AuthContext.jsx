import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (name, password) => {
    try {
      // Try to login
      const response = await api.post('/login', { name, password });
      const userData = response.data;
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return userData;
    } catch (error) {
       // If login fails (hopefully 401), we might try to register if we want that flow?
       // But typically we want explicit registration.
       // For this simple app, I'll assume explicit login and registration handled separately 
       // OR auto-registration as per original plan but now we have passwords.
       // With passwords, auto-registration on login is dangerous/confusing.
       // So I will stick to explicit Login vs Register OR just handle errors.
       throw error;
    }
  };

  const register = async (name, password) => {
      const response = await api.post('/users', { name, password });
      // After register, auto login?
      // For now just return the user, let component handle it.
      return response.data;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
