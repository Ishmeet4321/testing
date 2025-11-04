import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam';
import Recorder from '../components/Recorder';
import AudioPlayer from '../components/AudioPlayer';
import { runSpeechTherapy, generateFromPrompt, runTherapyLoop } from '../services/api';
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

  // --- Adaptive Reinforcement Loop Handler ---
  async function startRLLoop() {
    try {
      const resp = await runTherapyLoop();
      console.log("RL Therapy History:", resp.history);
      alert(`Therapy complete. Final score: ${resp.final_score.toFixed(2)}`);
    } catch (err) {
      console.error("Error running therapy loop:", err);
      alert("Error running adaptive therapy session.");
    }
  }

  // --- Audio recording handler ---
  async function onRecordingComplete(audioBlob) {
    setLastBlob(audioBlob);
    setTranscript('Processing...');

    // Capture webcam frame for emotion analysis
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

  // --- Generate a new practice sentence ---
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
          <p><strong>Prompt:</strong> Repeat the sentence shown or speak freely.</p>
          <Recorder onRecordingComplete={onRecordingComplete} mimeType="audio/webm" />
          <AudioPlayer blob={lastBlob} />
        </div>
      </div>

      {/* --- Language Selector --- */}
      <div className="card">
        <label>Interface language (TTS): </label>
        <select value={lang} onChange={(e) => setLang(e.target.value)}>
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
        {practice && <p><strong>Expected Emotion:</strong> {expectedEmotion.toUpperCase()}</p>}
        {detectedEmotion && <p><strong>Detected Emotion:</strong> {detectedEmotion.toUpperCase()}</p>}

        <ul>
          {feedback.length
            ? feedback.map((f, i) => <li key={i}>{f}</li>)
            : <li>No feedback yet</li>}
        </ul>

        <p><strong>Practice sentence:</strong> {practice || '—'}</p>

        {/* --- Action Buttons --- */}
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button onClick={() => speak(practice, lang)} disabled={!practice}>🔊 Play practice</button>
          <button onClick={requestPractice}>New sentence</button>
          <button onClick={startRLLoop}>Start Adaptive Therapy</button>
        </div>
      </div>
    </div>
  );
}
