import React, { useState } from 'react';

export default function Assistant() {
  const [audioBlob, setAudioBlob] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Optionally: use your own Recorder component here instead!
  const handleFileChange = (e) => {
    setAudioBlob(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!audioBlob) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    try {
      const resp = await fetch('/api/convo_assist', {
        method: 'POST',
        body: formData,
      });
      const data = await resp.json();
      setResult(data);
    } catch (err) {
      setResult({ error: 'Upload failed.' });
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <h1>Conversation Assistant</h1>
      <p>Record or upload a speech sample for instant ASR, translation, and feedback.</p>
      <input type="file" accept="audio/*" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={loading || !audioBlob}>
        {loading ? "Processing..." : "Analyze"}
      </button>
      {result && (
        <div style={{ marginTop: 20 }}>
          {result.error && <p style={{ color: "red" }}>{result.error}</p>}
          {result.asr_transcription && (
            <>
              <strong>ASR (Hindi):</strong> {result.asr_transcription}
              <br />
            </>
          )}
          {result.pron_score && (
            <>
              <strong>Pronunciation Score:</strong> {(result.pron_score * 100).toFixed(1)}%
              <br />
            </>
          )}
          {result.coherent_hindi && (
            <>
              <strong>Coherent Hindi:</strong> {result.coherent_hindi}
              <br />
            </>
          )}
          {result.english_translation && (
            <>
              <strong>English Translation:</strong> {result.english_translation}
              <br />
            </>
          )}
          {result.practice_sentence && (
            <>
              <strong>Practice Sentence:</strong> {result.practice_sentence}
              <br />
            </>
          )}
          {result.prosody_feedback && (
            <>
              <strong>Feedback:</strong>
              <ul>
                {Array.isArray(result.prosody_feedback) ?
                  result.prosody_feedback.map((fb, i) => <li key={i}>{fb}</li>)
                  : <li>{result.prosody_feedback}</li>}
              </ul>
            </>
          )}
          {result.prosody_metrics && (
            <>
              <strong>Prosody Metrics:</strong>
              <ul>
                <li>Pitch Mean: {result.prosody_metrics.pitch_mean}</li>
                <li>Pitch Var: {result.prosody_metrics.pitch_var}</li>
                <li>Energy Mean: {result.prosody_metrics.energy_mean}</li>
                <li>Energy Var: {result.prosody_metrics.energy_var}</li>
                <li>Speech Rate: {result.prosody_metrics.speech_rate}</li>
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
