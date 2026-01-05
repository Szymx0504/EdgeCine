import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Home from './pages/Home';
import Recommend from './pages/Recommend';
import Search from './pages/Search';
import Profile from './pages/Profile';

const CheckAuth = ({ children }) => {
  const { loading } = useAuth();
  if (loading) return <div>Loading...</div>;
  return children;
};

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route element={<CheckAuth><Layout /></CheckAuth>}>
        <Route path="/" element={<Home />} />
        <Route path="/recommend" element={<Recommend />} />
        <Route path="/search" element={<Search />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
    </Routes>
  );
}

export default App;