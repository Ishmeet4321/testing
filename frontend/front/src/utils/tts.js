export function speak(text, lang = "en-US") {
  const synth = window.speechSynthesis;
  if (!text || !synth) return;
  const utter = new window.SpeechSynthesisUtterance(text);

  // Try to select a matching voice
  const voices = synth.getVoices();
  const preferredVoice = voices.find(v => v.lang === lang) || voices[0];
  if (preferredVoice) utter.voice = preferredVoice;

  utter.lang = lang;
  synth.cancel();
  synth.speak(utter);
}


