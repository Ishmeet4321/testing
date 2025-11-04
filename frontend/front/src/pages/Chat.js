import React, { useState } from 'react';
import Recorder from '../components/Recorder';
import AudioPlayer from '../components/AudioPlayer';
import { runSpeechTherapy } from '../services/api';
import { convoAssistAPI } from '../services/api'; // or wherever your API file is

export default function Chat() {
  const [lastBlob, setLastBlob] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [score, setScore] = useState(null);
  const [translationEn, setTranslationEn] = useState('');
  const [backHindi, setBackHindi] = useState('');

  async function onRecordingComplete(blob) {
    setLastBlob(blob);
    setTranscript('Processing...');
    try {
      const resp = await convoAssistAPI(blob);
      setTranscript(resp.transcription || '');
      // Use resp.score or resp.confidence, based on your backend response!
      setScore(resp.score ?? resp.confidence ?? null);
      setTranslationEn(resp.translation_en || '');
      setBackHindi(resp.back_hindi || '');
    } catch (err) {
      console.error(err);
      setTranscript('Error processing audio.');
      setScore(null);
    }
  }

  return (
    <div>
      <h1>Conversation Assistant</h1>

      <div className="card">
        <Recorder onRecordingComplete={onRecordingComplete} mimeType="audio/webm" />
        <AudioPlayer blob={lastBlob} />
      </div>
    
      <div
        className="card"
        style={{
          marginTop: 28,
          padding: '18px 24px',
          fontSize: '0.98em',
          background: '#fcfcfd',
          border: '1px solid #eee',
          borderRadius: 11,
          minWidth: 320,
          maxWidth: 640,
        }}
      >
        <div style={{ margin: '4px 0' }}>
          <span role="img" aria-label="asr">📝</span> <b>ASR Transcription:</b>
          <span style={{ marginLeft: 7 }}>{transcript}</span>
        </div>
        <div style={{ margin: '4px 0' }}>
          <span role="img" aria-label="score">🔊</span> <b>Pronunciation Confidence:</b>
          <span style={{ marginLeft: 7 }}>{score !== null ? `${score.toFixed(2)}/100` : "—"}</span>
        </div>
        <div style={{ margin: '4px 0' }}>
          <span role="img" aria-label="en">🌐</span> <b>English Translation:</b>
          <span style={{ marginLeft: 7 }}>{translationEn || "—"}</span>
        </div>
        <div style={{ margin: '4px 0' }}>
          <span role="img" aria-label="backhi">🇮🇳</span> <b>Back to Hindi:</b>
          <span style={{ marginLeft: 7 }}>{backHindi || "—"}</span>
        </div>
      </div>
    </div>
  );
}

