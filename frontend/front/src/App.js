import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Practice from './pages/Practice';
//import Assistant from './pages/Assistant';
import Video from './pages/Video';
import Chat from './pages/Chat';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
//import EmotionPractice from './pages/EmotionPractice';

export default function App(){
  return (
    <div className="app">
      <Sidebar />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/practice" element={<Practice />} />
          <Route path="/video" element={<Video />} />
          
          <Route path="/chat" element={<Chat />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
