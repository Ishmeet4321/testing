import React, { useState } from 'react';
import Recorder from '../components/Recorder';
import AudioPlayer from '../components/AudioPlayer';
import { runSpeechTherapy, generateFromPrompt } from '../services/api';
import { speak } from '../utils/tts';

export default function Practice() {
  const [lastBlob, setLastBlob] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [score, setScore] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [practice, setPractice] = useState('');
  const [lang, setLang] = useState('hi-IN'); // speech synthesis lang

  async function onRecordingComplete(blob) {
    setLastBlob(blob);
    setTranscript('Processing...');
    try {
      // Send audio to the backend via runSpeechTherapy (speechtherapy API)
      const resp = await runSpeechTherapy(blob);
      setTranscript(resp.transcription || '');
      setScore(resp.score ?? null);
      setFeedback(resp.prosody?.feedback || []);
      setPractice(resp.prosody?.practice_sentence || '');
      // Speak the practice sentence if available
      if (resp.prosody?.practice_sentence) speak(resp.prosody.practice_sentence, lang);
    } catch (err) {
      console.error(err);
      setTranscript('Error processing audio.');
    }
  }

  const requestPractice = async () => {
    // Optionally generate new sentence from LLM
    const resp = await generateFromPrompt('एक सरल अभ्यास वाक्य बनाओ', 'hi');
    if (resp && resp.text) {
      setPractice(resp.text);
      speak(resp.text, lang);
    }
  };

  return (
    <div>
      <h1>Speech Practice</h1>

      <div className="card">
        <label>Interface language (TTS): </label>
        <select value={lang} onChange={(e) => setLang(e.target.value)}>
          <option value="hi-IN">Hindi (hi-IN)</option>
          <option value="en-US">English (en-US)</option>
        </select>
      </div>

      <div className="card">
        <p><strong>Prompt:</strong> Repeat the sentence shown or speak freely.</p>
        <Recorder onRecordingComplete={onRecordingComplete} mimeType="audio/webm" />
        <AudioPlayer blob={lastBlob} />
      </div>

      <div className="card">
        <h3>Transcription</h3>
        <p>{transcript || 'No transcription yet.'}</p>
      </div>

      <div className="card">
        <h3>Feedback</h3>
        {score !== null && <p>Pronunciation confidence: {(score * 100).toFixed(1)}%</p>}
        <ul>
          {feedback.length ? feedback.map((f, i) => <li key={i}>{f}</li>) : <li>No feedback yet</li>}
        </ul>
        <p><strong>Practice sentence:</strong> {practice || '—'}</p>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => speak(practice, lang)} disabled={!practice}>🔊 Play practice</button>
          <button onClick={requestPractice}>New sentence</button>
        </div>
      </div>
    </div>
  );
}
