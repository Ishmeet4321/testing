// src/components/Recorder.js
import React, { useRef, useState } from 'react';

export default function Recorder({ onRecordingComplete, mimeType='audio/webm' }) {
  const mediaRef = useRef(null);
  const recRef = useRef(null);
  const [recording, setRecording] = useState(false);

  async function start() {
    if (!navigator.mediaDevices) {
      alert('No microphone access in this browser.');
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRef.current = stream;
    recRef.current = new MediaRecorder(stream, { mimeType });
    const chunks = [];
    recRef.current.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    recRef.current.onstop = () => {
      const blob = new Blob(chunks, { type: mimeType });
      onRecordingComplete && onRecordingComplete(blob);
      // stop tracks
      stream.getTracks().forEach(t => t.stop());
    };
    recRef.current.start();
    setRecording(true);
  }

  function stop() {
    if (recRef.current && recRef.current.state !== 'inactive') {
      recRef.current.stop();
      setRecording(false);
    }
  }

  return (
    <div style={{display:'flex', gap:8, alignItems:'center'}}>
      <button onClick={start} disabled={recording}>Start</button>
      <button onClick={stop} disabled={!recording}>Stop</button>
      <span>{recording ? 'Recording…' : 'Idle'}</span>
    </div>
  );
}
