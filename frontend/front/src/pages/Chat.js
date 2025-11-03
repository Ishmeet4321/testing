// src/pages/Chat.js
import React, { useState } from 'react';
import { generateFromPrompt } from '../services/api';
import { speak } from '../utils/tts';

export default function Chat(){
  const [lang, setLang] = useState('hi');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([{ role: 'assistant', text: 'नमस्ते — कैसे मदद करूं?' }]);

  const send = async () => {
    if (!input.trim()) return;
    setMessages(m=>[...m, {role:'user', text: input}]);
    setInput('');
    const prompt = input;
    const res = await generateFromPrompt(prompt, lang);
    const reply = res.text || '—';
    setMessages(m=>[...m, {role:'assistant', text: reply}]);
    // Speak reply using language code mapping
    const ttsLang = lang === 'hi' ? 'hi-IN' : 'en-US';
    speak(reply, ttsLang);
  };

  return (
    <div>
      <h1>Conversation Assistant</h1>
      <div className="card">
        <div style={{display:'flex', gap:12, marginBottom:8}}>
          <label>Model language:</label>
          <select value={lang} onChange={(e)=>setLang(e.target.value)}>
            <option value="hi">Hindi</option>
            <option value="en">English</option>
          </select>
        </div>

        <div style={{height:320, overflow:'auto', border:'1px solid #eee', padding:8, marginBottom:8}}>
          {messages.map((m,i)=>(
            <div key={i} style={{textAlign: m.role==='user' ? 'right' : 'left', margin:'6px 0'}}>
              <strong>{m.role==='user' ? 'You' : 'Assistant'}</strong>: {m.text}
            </div>
          ))}
        </div>

        <div style={{display:'flex', gap:8}}>
          <input value={input} onChange={(e)=>setInput(e.target.value)} style={{flex:1}} placeholder={lang==='hi' ? 'Type in Hindi...' : 'Type in English...'} />
          <button onClick={send}>Send</button>
        </div>
      </div>
    </div>
  );
}
