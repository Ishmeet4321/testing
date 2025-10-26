export function speak(text, lang = "en-US") {
  const synth = window.speechSynthesis;
  if (!text || !synth) return;
  const utter = new window.SpeechSynthesisUtterance(text);
  utter.lang = lang;
  synth.cancel();
  synth.speak(utter);
}
