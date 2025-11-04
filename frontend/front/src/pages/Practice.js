import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam';
import Recorder from '../components/Recorder';
import AudioPlayer from '../components/AudioPlayer';
import { runSpeechTherapy, generateFromPrompt, runTherapyStep } from '../services/api';
import { speak } from '../utils/tts';

export default function Practice() {
  const webcamRef = useRef(null);
  const [lastBlob, setLastBlob] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [score, setScore] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [practice, setPractice] = useState('');
  const [expectedEmotion, setExpectedEmotion] = useState('');
  const [detectedEmotion, setDetectedEmotion] = useState('');
  const [lang, setLang] = useState('hi-IN');
  const [targetArea, setTargetArea] = useState('general');
  
  // NEW RL STATES
  const [rlHistory, setRlHistory] = useState([]); // Array to store history of steps
  const [rlRunning, setRlRunning] = useState(false); // Flag for RL mode
  const [rlIteration, setRlIteration] = useState(0); // Current RL step number
  const [rlPrompt, setRlPrompt] = useState(''); // Prompt for the current RL step

  const MAX_ITERATIONS = 3;

  // --- RL Step Handler (Triggers on Recording Complete ONLY when rlRunning is true) ---
  async function onRlRecordingComplete(audioBlob) {
    setLastBlob(audioBlob);
    setTranscript('Processing...');

    try {
      // 1. Send the audio to the single-step RL API
      const resp = await runTherapyStep(audioBlob, rlIteration);
      
      if (resp.status === "error") {
        throw new Error(resp.message);
      }

      // 2. Update frontend state and history
      const newHistoryItem = { 
        iteration: resp.iteration, 
        metrics: resp.metrics, 
        reward: resp.reward,
        weakest: resp.weakest_feature
      };
      setRlHistory(prev => [...prev, newHistoryItem]);
      setTranscript(resp.metrics.transcription || 'Analysis complete.');
      setScore(resp.metrics.conf_score || null);

      // 3. Check for termination condition
      if (resp.is_complete || resp.iteration >= MAX_ITERATIONS) {
        setRlRunning(false);
        setRlPrompt('✅ Adaptive Therapy Complete. Check results below.');
        alert(`Adaptive Therapy Complete after ${resp.iteration} iterations! Final Reward: ${resp.reward.toFixed(3)}`);
        
        const sessionName = `Session_${+new Date()}`; // or keep a simple counter
        const finishedSession = {
          name: sessionName,
          results: [...rlHistory, { 
            iteration: resp.iteration, 
            metrics: resp.metrics, 
            reward: resp.reward,
            weakest: resp.weakest_feature
          }],
          finalReward: resp.reward
        };
        // Load previous sessions
        const prev = JSON.parse(localStorage.getItem('therapy_sessions') || '[]');
        localStorage.setItem('therapy_sessions', JSON.stringify([...prev, finishedSession]));
        return;
      }

      // 4. Set the next prompt and update iteration count
      const nextIteration = resp.iteration + 1;
      setRlIteration(nextIteration);
      setRlPrompt(resp.next_prompt);
      setExpectedEmotion(resp.expected_emotion);
      
      // Speak the next prompt immediately for the user
      speak(resp.next_prompt, lang);
      
      alert(`Iteration ${nextIteration}: Please repeat the new sentence now: "${resp.next_prompt}"`);
      
    } catch (err) {
      console.error("Error during RL step:", err);
      setRlRunning(false);
      setRlPrompt('❌ Error. Please check console.');
    }
  }

  // --- Initial RL Loop Starter ---
  async function startRLLoop() {
    setRlHistory([]); // Clear previous history
    setRlRunning(true);
    setRlIteration(1);
    
    // 1. Get initial practice sentence (using the existing generate route for simplicity)
    const initialPromptResp = await generateFromPrompt(targetArea, lang === 'hi-IN' ? 'hi' : 'en');
    const initialSentence = initialPromptResp.text;
    const initialEmotion = initialPromptResp.expected_emotion;

    setRlPrompt(initialSentence);
    setExpectedEmotion(initialEmotion);
    speak(initialSentence, lang);
    
    alert(`Adaptive Therapy Started! Iteration 1: Please repeat the sentence now: "${initialSentence}"`);
  }

  // --- Normal Practice Mode Handler (Uses separate API calls) ---
  async function onNormalRecordingComplete(audioBlob) {
    // This is the old, non-RL logic. We keep it separate.
    setLastBlob(audioBlob);
    setTranscript('Processing...');

    let imageBlob = null;
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        const fetchRes = await fetch(imageSrc);
        imageBlob = await fetchRes.blob();
      }
    }

    try {
      const resp = await runSpeechTherapy(audioBlob, imageBlob, expectedEmotion);
      setTranscript(resp.transcription || '');
      setScore(resp.score ?? null);
      setFeedback(resp.feedback || []);
      setTargetArea(resp.target_area || 'general');
      setDetectedEmotion(resp.detected_emotion || '');
    } catch (err) {
      console.error(err);
      setTranscript('Error processing audio.');
      setDetectedEmotion('');
    }
  }

  const requestPractice = async () => {
    try {
      const backendLang = lang === 'hi-IN' ? 'hi' : 'en';
      const resp = await generateFromPrompt(targetArea, backendLang);

      const blockList = ['अपनी भाषा', 'आप कोई भी', 'choose any', 'speak any word'];

      if (resp && resp.text && !blockList.some(x => resp.text.includes(x))) {
        setPractice(resp.text);
        setExpectedEmotion(resp.expected_emotion || 'general');
        speak(resp.text, lang);
      } else {
        setPractice('');
        setExpectedEmotion('');
        alert('No valid practice sentence generated. Please try again!');
      }
    } catch (err) {
      console.error('Error requesting practice:', err);
      setExpectedEmotion('');
    }
  };

  return (
    <div>
      <h1>Speech Practice</h1>

      {/* --- Webcam and Recording Section --- */}
      <div className="card" style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
        <div>
          <h3>Video Feed for Emotion</h3>
          <Webcam
            audio={false}
            mirrored
            ref={webcamRef}
            width={320}
            height={240}
            screenshotFormat="image/jpeg"
            style={{ borderRadius: 8, border: '1px solid #ccc' }}
          />
        </div>

        <div>
          <h3>Recording</h3>
          {/* CRITICAL CHANGE: Use different handlers based on mode */}
          <p><strong>Prompt:</strong> {rlRunning ? `(RL Iteration ${rlIteration}/${MAX_ITERATIONS})` : `(Normal Mode)`} Repeat the sentence shown.</p>
          <Recorder 
            onRecordingComplete={rlRunning ? onRlRecordingComplete : onNormalRecordingComplete} 
            mimeType="audio/webm" 
            disabled={rlRunning && rlIteration > MAX_ITERATIONS}
          />
          <AudioPlayer blob={lastBlob} />
        </div>
      </div>

      {/* --- Language Selector --- */}
      <div className="card">
        <label>Interface language (TTS): </label>
        <select value={lang} onChange={(e) => setLang(e.target.value)} disabled={rlRunning}>
          <option value="hi-IN">Hindi (hi-IN)</option>
          <option value="en-US">English (en-US)</option>
        </select>
      </div>

      {/* --- Transcription --- */}
      <div className="card">
        <h3>Transcription</h3>
        <p>{transcript || 'No transcription yet.'}</p>
      </div>

      {/* --- Feedback Section --- */}
      <div className="card">
        <h3>Feedback</h3>
        {score !== null && <p>Pronunciation confidence: {(score * 100).toFixed(1)}%</p>}
        {/* Display RL prompt or normal practice sentence */}
        <p><strong>Practice sentence:</strong> {rlRunning ? rlPrompt : practice || '—'}</p>
        
        {/* Show emotion details only in normal mode */}
        {!rlRunning && practice && <p><strong>Expected Emotion:</strong> {expectedEmotion.toUpperCase()}</p>}
        {!rlRunning && detectedEmotion && <p><strong>Detected Emotion:</strong> {detectedEmotion.toUpperCase()}</p>}

        {/* Show normal feedback or a message during RL mode */}
        {rlRunning ? (
             <p>Results will be tallied and shown below after the session is complete.</p>
        ) : (
            <ul>
                {feedback.length ? feedback.map((f, i) => <li key={i}>{f}</li>) : <li>No feedback yet</li>}
            </ul>
        )}

        {/* --- Action Buttons --- */}
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button onClick={() => speak(rlRunning ? rlPrompt : practice, lang)} disabled={!rlPrompt && !practice}>🔊 Play prompt</button>
          <button onClick={requestPractice} disabled={rlRunning}>New sentence</button>
          <button onClick={startRLLoop} disabled={rlRunning}>
            Start Adaptive Therapy
          </button>
        </div>
      </div>
      
      {/* RL History Display */}
      {rlHistory.length > 0 && (
        <div className="card" style={{ marginTop: 20 }}>
            <h3>Adaptive Therapy Session Results (Steps: {rlHistory.length})</h3>
            <p><strong>Final Reward:</strong> {rlHistory.at(-1)?.reward.toFixed(3)}</p>
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
                    {rlHistory.map((item) => (
                        <tr key={item.iteration}>
                            <td>{item.iteration}</td>
                            <td>{item.reward.toFixed(3)}</td>
                            <td>{item.weakest}</td>
                            <td>{item.metrics.pitch_var.toFixed(2)}</td>
                            <td>{item.metrics.energy_mean.toFixed(3)}</td>
                            <td>{item.metrics.speech_rate.toFixed(2)}</td>
                            <td>{item.metrics.conf_score.toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
      )}
    </div>
  );
}