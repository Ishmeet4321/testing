import React, { useEffect, useState } from 'react';

export default function Dashboard(){
    const [sessions, setSessions] = useState([]);

  useEffect(() => {
    // Load saved sessions on mount from localStorage
    const saved = JSON.parse(localStorage.getItem('therapy_sessions') || '[]');
    setSessions(saved);
  }, []);
  
  return (
    <div>
      <h1>Dashboard</h1>
      <div className="card">
        <h3>Welcome</h3>
        <p>Track progress, start practice sessions, and review previous reports.</p>
      </div>
      <div className="card">
        <h4>Quick Actions</h4>
        <p>Start a Practice or open the Conversation Assistant from the sidebar.</p>
      </div>

      <div className="card">
          <h4>Therapy Sessions</h4>
          {sessions.length === 0 && <p>No completed sessions yet.</p>}
          {sessions.map((session, idx) => (
            <div key={idx} style={{marginBottom:30}}>
              <h5>{`Session ${idx+1}`}</h5>
              <strong>Final Reward:</strong> {session.finalReward.toFixed(3)}
              <table>
                <thead>
                  <tr>
                    <th>Iter</th>
                    <th>Reward</th>
                    <th>Weakest Feature</th>
                    <th>Pitch Var</th>
                    <th>Energy Mean</th>
                    <th>Rate</th>
                    <th>Conf Score</th>
                  </tr>
                </thead>
                <tbody>
                  {session.results.map(row => (
                    <tr key={row.iteration}>
                      <td>{row.iteration}</td>
                      <td>{row.reward.toFixed(3)}</td>
                      <td>{row.weakest}</td>
                      <td>{row.metrics.pitch_var.toFixed(2)}</td>
                      <td>{row.metrics.energy_mean.toFixed(3)}</td>
                      <td>{row.metrics.speech_rate.toFixed(2)}</td>
                      <td>{row.metrics.conf_score.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      </div>
  );
}
