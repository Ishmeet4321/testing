import os
import random
import torch
import torch.nn.functional as F
import torchaudio
import librosa
import numpy as np
import sounddevice as sd

from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC, AutoTokenizer, AutoModelForCausalLM, pipeline, MarianMTModel, MarianTokenizer
from scipy.io.wavfile import write

import csv
import time

# English translation model + tokenizer
translator_name = "Helsinki-NLP/opus-mt-hi-en"
tokenizer = MarianTokenizer.from_pretrained(translator_name)
translator = MarianMTModel.from_pretrained(translator_name)

# Back to Hindi model + tokenizer
hindi_trans = "Helsinki-NLP/opus-mt-en-hi"
hin_tok = MarianTokenizer.from_pretrained(hindi_trans)
hin_translator = MarianMTModel.from_pretrained(hindi_trans)

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

def translate_to_english(transcription_text):
    if not transcription_text.strip():
        return ""
    inputs = tokenizer(transcription_text, return_tensors="pt", padding=True, truncation=True)
    translated = translator.generate(**inputs, max_length=512)
    english_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    return english_text

def translate_to_hindi(english_text):
    if not english_text.strip():
        return ""
    inputs = hin_tok(english_text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = hin_translator.generate(**inputs, max_length=512)
    return hin_tok.decode(outputs[0], skip_special_tokens=True).strip()
