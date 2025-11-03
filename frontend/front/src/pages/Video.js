// src/pages/Video.js
import React, { useRef, useState, useEffect } from 'react';
import Webcam from 'react-webcam';
import { detectEmotion } from '../services/api';
import { speak } from '../utils/tts';

export default function Video() {
  const webcamRef = useRef(null);
  const [running, setRunning] = useState(false);
  const [emotion, setEmotion] = useState(null);
  const [intervalMs] = useState(1500); // send frame every 1.5s

  useEffect(() => {
    let handle;
    if (running) {
      handle = setInterval(async () => {
        if (!webcamRef.current) return;
        const canvas = webcamRef.current.getCanvas();
        if (!canvas) return;
        canvas.toBlob(async (blob) => {
          try {
            // Use the detectEmotion function which calls your Flask backend
            const res = await detectEmotion(blob);
            if (res && res.emotion) {
              if (res.emotion !== emotion) {
                setEmotion(res.emotion);
                speak(`Detected emotion ${res.emotion}`, 'en-US');
              }
            }
          } catch (err) {
            console.error(err);
          }
        }, 'image/jpeg', 0.8);
      }, intervalMs);
    }
    return () => clearInterval(handle);
  }, [running, intervalMs, emotion]);

  return (
    <div>
      <h1>Video Analysis</h1>
      <div className="card">
        <Webcam audio={false} mirrored ref={webcamRef} width={640} height={480} />
        <div style={{marginTop:12}}>
          <button onClick={() => setRunning(r => !r)}>
            {running ? 'Stop' : 'Start'} analysis
          </button>
          <span style={{marginLeft:12}}>Emotion: {emotion || '—'}</span>
        </div>
      </div>
    </div>
  );
}
