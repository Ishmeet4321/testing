import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Practice from './pages/Practice';
import Video from './pages/Video';
import Chat from './pages/Chat';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Signup from './pages/Signup'; 
import Login from './pages/Login';  

export default function App(){
  const [token, setToken] = useState(localStorage.getItem('token') || '');

  function handleSetToken(tok) {
    setToken(tok);
    localStorage.setItem('token', tok);
  }

  function ProtectedRoute({ children }) {
    return token ? children : <Navigate to="/login" replace />;
  }

  return (
    <div className="app">
      <Sidebar />
      <main className="main">
        <Routes>
          <Route path="/login" element={<Login setToken={handleSetToken} />} />
          <Route path="/signup" element={<Signup />} />

          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/practice" element={<ProtectedRoute><Practice /></ProtectedRoute>} />
          <Route path="/video" element={<ProtectedRoute><Video /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings setToken={handleSetToken} /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  );
}
