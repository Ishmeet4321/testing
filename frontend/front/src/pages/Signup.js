import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';


export default function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');
  const navigate = useNavigate();


  async function handleSignup(e) {
    e.preventDefault();
    setMsg(''); // clear before request
    try {
      const resp = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await resp.json();
      if (resp.ok) {
        setMsg('Signup successful! Redirecting...');
        setTimeout(() => navigate('/login'), 1200);
      } else {
        setMsg(data.error || 'Signup failed');
      }
    } catch (e) {
      setMsg('Network or server error');
      console.error(e);
    }
  }

  return (
    <form onSubmit={handleSignup}>
      <h2>Sign Up</h2>
      <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required />
      <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
      <button type="submit">Sign up</button>
      <div>{msg}</div>
      <p>Already have an account? <a href="/login">Login here</a></p>
    </form>
  );
}
