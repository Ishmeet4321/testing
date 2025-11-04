import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
  timeout: 12000000,
});

// CHANGED: Accept an imageBlob and expectedEmotion string
export async function runSpeechTherapy(audioBlob, imageBlob, expectedEmotion) {
  const fd = new FormData();
  fd.append("audio", audioBlob, "recording.wav");
  
  // NEW: Append image and expected emotion
  if (imageBlob) {
    fd.append("image", imageBlob, "image.jpg");
  }
  if (expectedEmotion) {
    fd.append("expected_emotion", expectedEmotion);
  }

  const res = await API.post("/speechtherapy", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function runTherapyLoop(audioPath = null) {
  const res = await API.post("/therapy_loop", { audio_path: audioPath });
  return res.data;
}

export async function transcribeAudio(audioBlob) {
  const fd = new FormData();
  fd.append("audio", audioBlob, "recording.wav");
  const res = await API.post("/transcribe", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function detectEmotion(imageFile) {
  const fd = new FormData();
  fd.append("image", imageFile, "image.jpg");
  const res = await API.post("/emotion", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function translateHindi(hindiText) {
  const res = await API.post("/translate", { hindi: hindiText });
  return res.data;
}

export async function analyzeVideoLandmarks(videoFile) {
  const fd = new FormData();
  fd.append("video", videoFile, "video.mp4");
  const res = await API.post("/videolandmark", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function generateFromPrompt(prompt, lang) {
  const res = await API.post("/generate", { prompt, lang });
  return res.data;
}

export async function convoAssistAPI(audioBlob) {
  const fd = new FormData();
  fd.append("audio", audioBlob, "recording.wav");
  const res = await API.post("/convo_assist", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}



export async function extractAudioFeatures(audioBlob) {
  const fd = new FormData();
  fd.append("audio", audioBlob, "recording.wav");
  const res = await API.post("/audiopreproc", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export default API;