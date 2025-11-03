import React from 'react';

export default function Settings(){
  return (
    <div>
      <h1>Settings</h1>
      <div className="card">
        <p>Language: <select><option>Hindi</option><option>English</option></select></p>
        <p>Theme: <select><option>Light</option><option>Dark</option></select></p>
      </div>
    </div>
  );
}
