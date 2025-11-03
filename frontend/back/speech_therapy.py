import os
import random
import torch
import torch.nn.functional as F
import torchaudio
import librosa
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC, AutoTokenizer, AutoModelForCausalLM
import sounddevice as sd
from scipy.io.wavfile import write
import csv
import time
import re

# Global variables for lazy loading
tokenizer = None
lm_model = None

def _load_lingo_models():
    """Lazy load Lingo models only when first needed"""
    global tokenizer, lm_model
    if tokenizer is None or lm_model is None:
        lm_model_name = "LingoIITGN/ganga-1b"
        tokenizer = AutoTokenizer.from_pretrained(lm_model_name)
        lm_model = AutoModelForCausalLM.from_pretrained(lm_model_name)

def record_audio(duration=5, fs=16000, target_rms=0.03, output_path="recorded_audio.wav"):
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    rms = np.sqrt(np.mean(recording ** 2))
    if rms == 0:  # Avoid division by zero
        scaling_factor = 1
    else:
        scaling_factor = target_rms / rms
    recording *= scaling_factor
    write(output_path, fs, (recording * 32767).astype(np.int16))
    print(f"Audio saved to {output_path} with normalized RMS {target_rms}")
    return output_path

def get_pronunciation_score(audio_path):
    # Use the original model and processor
    processor = Wav2Vec2Processor.from_pretrained("Harveenchadha/vakyansh-wav2vec2-hindi-him-4200")
    model = Wav2Vec2ForCTC.from_pretrained("Harveenchadha/vakyansh-wav2vec2-hindi-him-4200")

    # Load and process audio
    y, sr = librosa.load(audio_path, sr=16000)
    inputs = processor(y, sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(inputs.input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    predicted_text = processor.tokenizer.decode(predicted_ids[0])
    import re
    cleaned = re.sub(r"<[^>]+>", "", predicted_text).strip()
    probs = F.softmax(logits, dim=-1)
    chosen_probs = probs.gather(-1, predicted_ids.unsqueeze(-1)).squeeze(-1)
    score = float(chosen_probs.mean().item()) * 100
    return cleaned, score


def analyze_prosody(audio_path):
    y, sr = librosa.load(audio_path, sr=16000)
    
    # Extract pitch
    try:
        f0, _, _ = librosa.pyin(y, fmin=80, fmax=300, sr=sr)
        f0 = f0[~np.isnan(f0)]
    except Exception as e:
        print(f"WARN: Pitch extraction failed: {e}")
        f0 = np.array([])
    pitch_mean = np.mean(f0) if len(f0) > 0 else 0
    pitch_var = np.var(f0) if len(f0) > 0 else 0

    # Extract energy
    try:
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = np.mean(rms) if len(rms) > 0 else 0
        energy_var = np.var(rms) if len(rms) > 0 else 0
    except Exception as e:
        print(f"WARN: Energy extraction failed: {e}")
        energy_mean, energy_var = 0, 0

    # Calculate speech rate
    speech_rate = len(f0) / (len(y)/sr) if len(y) > 0 else 0

    # Generate feedback AND determine which area needs improvement
    feedback = []
    target_area = "general"  # NEW: Track what the user needs to work on
    
    if pitch_var < 50 and pitch_mean > 0:
        feedback.append("Your pitch is very flat. Try adding more intonation and variation in your voice.")
        target_area = "pitch"
    elif pitch_var > 200:
        feedback.append("Great! You have good pitch variation.")
    
    if energy_mean < 0.02:
        feedback.append("Your voice is too soft. Try speaking louder and with more energy.")
        target_area = "energy"
    elif energy_mean > 0.05:
        feedback.append("Good energy! Keep speaking with this confidence.")
    
    if speech_rate < 2 and speech_rate > 0:
        feedback.append("You are speaking too slowly. Try to increase your pace.")
        target_area = "rate"
    elif speech_rate > 4:
        feedback.append("You are speaking quite fast. Try to slow down a bit for clarity.")
    
    if not feedback:
        feedback.append("Good attempt! Keep practicing.")

    return {
        "pitch_mean": pitch_mean,
        "pitch_var": pitch_var,
        "energy_mean": energy_mean,
        "energy_var": energy_var,
        "speech_rate": speech_rate,
        "feedback": feedback,
        "target_area": target_area  # NEW: Return what to work on
    }

def generate_practice_sentence(feature="general"):
    """
    Generate a truly random, Lingo-model-based sentence tailored to the user's weak speech field.
    No string-based fallbacks. Every sentence is a new Ganga model completion.
    """
    _load_lingo_models()
    import random

    prompt_patterns = {
        "pitch": [
            "ऐसा हिंदी वाक्य जनरेट करें जिसमें आवाज़ का उतार-चढ़ाव आ सके।",
            "एक अभ्यास हिंदी वाक्य जिससे बोलने में उच्चारण बदल सके।",
            "ऐसा वाक्य जो पढ़ते समय intonation सुधार सके।"
        ],
        "energy": [
            "एक हिंदी वाक्य बनाओ जिसे बहुत ऊर्जा और उत्साह के साथ बोला जाए।",
            "ऐसा हिंदी वाक्य जनरेट करें जिसे तेज़ और ज़ोर से बोला जा सके।",
            "एक ऐसी लाइन हिंदी में दे जो डाइनामिक या expressively बोली जाती हो।"
        ],
        "rate": [
            "ऐसा हिंदी वाक्य बनाओ जिसे आराम से, धीरे-धीरे और साफ़ बोले जा सके।",
            "एक हिंदी वाक्य जनरेट करें जिससे बोलने की गति बेहतर हो सके।",
            "एक लाइन जो सोचकर और धीरे-धीरे बोली जाती है।"
        ],
        "general": [
            "कोई भी हिंदी प्रैक्टिस वाक्य जनरेट करें जो आम बोलचाल में आता हो।",
            "एक सरल, असली जीवन में बोलने वाला हिंदी वाक्य जनरेट करें।",
            "कोई knowledge बढ़ाने वाला हिंदी वाक्य जनरेट करें।"
        ]
    }

    # Always randomize the prompt pattern to help prevent repetitive model outputs
    prompt = random.choice(prompt_patterns.get(feature, prompt_patterns["general"]))
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(lm_model.device)
        if "token_type_ids" in inputs: del inputs["token_type_ids"]

        with torch.no_grad():
            outputs = lm_model.generate(
                **inputs,
                max_new_tokens=20,
                do_sample=True,
                top_k=50,
                top_p=0.97,   # maximize diversity
                temperature=1.0,   # high randomness
                num_beams=1
            )
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        sentence = text.replace(prompt, "").strip()
        # Clean up: get just the first sentence (split at purna-viram etc)
        for punct in ['।', '?', '!']:
            if punct in sentence:
                sentence = sentence.split(punct)[0] + punct
                break

        if not sentence or len(sentence.split()) < 3:
            # Try again, up to two model attempts (never pick a fixed fallback!)
            prompt = random.choice(prompt_patterns.get(feature, prompt_patterns["general"]))
            inputs = tokenizer(prompt, return_tensors="pt").to(lm_model.device)
            if "token_type_ids" in inputs: del inputs["token_type_ids"]
            with torch.no_grad():
                outputs = lm_model.generate(
                    **inputs,
                    max_new_tokens=18,
                    do_sample=True,
                    top_k=50,
                    top_p=0.97,
                    temperature=1.0,
                    num_beams=1
                )
            text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            sentence = text.replace(prompt, "").strip()
            for punct in ['।', '?', '!']:
                if punct in sentence:
                    sentence = sentence.split(punct)[0] + punct
                    break
        # Final fallback: if both completions fail, return a short "try again" type text, never a list-based sentence!
        return sentence if sentence and len(sentence.split()) >= 3 else "कृपया फिर से प्रयास करें।"
    except Exception as e:
        return "कृपया फिर से प्रयास करें।"

