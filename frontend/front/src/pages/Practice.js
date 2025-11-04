import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam'; // ADDED
import Recorder from '../components/Recorder';
import AudioPlayer from '../components/AudioPlayer';
import { runSpeechTherapy, generateFromPrompt } from '../services/api';
import { speak } from '../utils/tts';


export default function Practice() {
  const webcamRef = useRef(null); // NEW: Webcam reference
  const [lastBlob, setLastBlob] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [score, setScore] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [practice, setPractice] = useState('');
  const [expectedEmotion, setExpectedEmotion] = useState(''); // NEW
  const [detectedEmotion, setDetectedEmotion] = useState(''); // NEW
  const [lang, setLang] = useState('hi-IN');
  const [targetArea, setTargetArea] = useState('general');


  async function onRecordingComplete(audioBlob) {
    setLastBlob(audioBlob);
    setTranscript('Processing...');
    
    // NEW: Capture image from webcam
    let imageBlob = null;
    if (webcamRef.current) {
        // Get the image as base64 string
        const imageSrc = webcamRef.current.getScreenshot();
        if (imageSrc) {
            // Convert base64 imageSrc to a Blob
            const fetchRes = await fetch(imageSrc);
            imageBlob = await fetchRes.blob();
        }
    }
    
    try {
      // CHANGED: Pass audioBlob, imageBlob, and the expectedEmotion
      const resp = await runSpeechTherapy(audioBlob, imageBlob, expectedEmotion); 

      setTranscript(resp.transcription || '');
      setScore(resp.score ?? null);
      setFeedback(resp.feedback || []);
      setTargetArea(resp.target_area || 'general');
      setDetectedEmotion(resp.detected_emotion || ''); // NEW
      
    } catch (err) {
      console.error(err);
      setTranscript('Error processing audio.');
      setDetectedEmotion('');
    }
  }


  const requestPractice = async () => {
    try {
      const backendLang = lang === 'hi-IN' ? 'hi' : 'en';
      // CHANGED: generateFromPrompt now returns text AND expected_emotion
      const resp = await generateFromPrompt(targetArea, backendLang);

      // Simple check for typical instructions (customize as needed)
      const blockList = [
        'अपनी भाषा', 'आप कोई भी', 'choose any', 'speak any word'
      ];
      
      if (resp && resp.text && !blockList.some(x => resp.text.includes(x))) {
        setPractice(resp.text);
        setExpectedEmotion(resp.expected_emotion || 'general'); // NEW
        speak(resp.text, lang);
      } else {
        setPractice('');
        setExpectedEmotion(''); // Clear expected emotion on error
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
      
      {/* NEW: Webcam setup */}
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
      
      
      <div className="card">
        <label>Interface language (TTS): </label>
        <select value={lang} onChange={(e) => setLang(e.target.value)}>
          <option value="hi-IN">Hindi (hi-IN)</option>
          <option value="en-US">English (en-US)</option>
        </select>
      </div>


      <div className="card">
        <h3>Transcription</h3>
        <p>{transcript || 'No transcription yet.'}</p>
      </div>


      <div className="card">
        <h3>Feedback</h3>
        {score !== null && <p>Pronunciation confidence: {(score * 100).toFixed(1)}%</p>}
        {/* NEW: Display emotion information */}
        {practice && <p><strong>Expected Emotion:</strong> {expectedEmotion.toUpperCase()}</p>}
        {detectedEmotion && <p><strong>Detected Emotion:</strong> {detectedEmotion.toUpperCase()}</p>}
        
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