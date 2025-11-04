import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Settings({ setToken }) {
  const navigate = useNavigate();

  function handleLogout() {
    setToken('');
    localStorage.removeItem('token');
    navigate('/login', { replace: true });
  }

  return (
    <div>
      <h1>Settings</h1>
      <div className="card">
        <p>Language: <select><option>Hindi</option><option>English</option></select></p>
        <p>Theme: <select><option>Light</option><option>Dark</option></select></p>
        <button
          onClick={handleLogout}
          style={{
            marginTop: '24px',
            padding: '8px 20px',
            background: '#7041aa',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Logout
        </button>
      </div>
    </div>
  );
}
