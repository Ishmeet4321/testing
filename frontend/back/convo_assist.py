import os
import random
import torch
import torch.nn.functional as F
import torchaudio
import librosa
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC, AutoTokenizer, AutoModelForCausalLM, pipeline, MarianMTModel, MarianTokenizer
from speech_therapy import get_pronunciation_score, analyze_prosody

import sounddevice as sd
from scipy.io.wavfile import write
import csv
import time
asr_model_name = "Harveenchadha/vakyansh-wav2vec2-hindi-him-4200"
processor = Wav2Vec2Processor.from_pretrained(asr_model_name)
asr_model = Wav2Vec2ForCTC.from_pretrained(asr_model_name)

lm_model_name = "LingoIITGN/ganga-1b"
tokenizer = AutoTokenizer.from_pretrained(lm_model_name)
lm_model = AutoModelForCausalLM.from_pretrained(lm_model_name)

# translator = pipeline("translation", model="Helsinki-NLP/opus-mt-hi-en")
translator_name = "Helsinki-NLP/opus-mt-hi-en"
tokenizer = MarianTokenizer.from_pretrained(translator_name)
translator = MarianMTModel.from_pretrained(translator_name)


def translate_to_english(hindi_text):
    if not hindi_text.strip():
        return ""
    
    # Tokenize the Hindi text
    inputs = tokenizer(hindi_text, return_tensors="pt", padding=True, truncation=True)
    
    # Generate translation (max_length here is valid)
    translated = translator.generate(**inputs, max_length=512)
    
    # Decode the generated tokens
    english_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    return english_text
import re
import torch

def correct_incoherent_hindi(incoherent_text):
    """
    Uses the Ganga-1B language model to infer and correct an incoherent/fragmented 
    Hindi sentence into a coherent, simple one.
    
    Enhancements: Added a pre-cleaning step for common Hinglish words/fragments,
    and slightly adjusted generation parameters for better LLM adherence.
    """
    if not incoherent_text.strip():
        return "अस्पष्ट संदेश"
    
    # --- Pre-cleaning/Filtering of common non-Hindi fragments (Hinglish) ---
    # This helps the LLM focus on the intended meaning rather than noise.
    cleaned_text = re.sub(r'\b(me|ko|hai|ho|main|i|am|the|is|a)\b', '', incoherent_text, flags=re.IGNORECASE).strip()
    if not cleaned_text:
        cleaned_text = incoherent_text # Revert if pre-cleaning made it empty
        
    # The prompt asks the model to rephrase the fragmented text into a clear, single Hindi sentence.
    prompt = (
        f"एक भाषण बाधित रोगी ने यह अस्पष्ट वाक्य कहा: '{cleaned_text}'। "
        "इसका सबसे संभावित और सरल अर्थ एक ही स्पष्ट हिंदी वाक्य में बताओ। "
        "कोई अंग्रेजी शब्द या अनुवाद शामिल नहीं करना है। "
        "उदाहरण: 'पानी me hai' को 'मुझे पानी चाहिए।' में बदलें। उत्तर केवल एक वाक्य में समाप्त होना चाहिए।"
    )
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
        inputs = {k: v.to(lm_model.device) for k, v in inputs.items()}
        if "token_type_ids" in inputs:
            del inputs["token_type_ids"]

        # Generate text: Use Beam Search for reliable coherence
        with torch.no_grad():
            outputs = lm_model.generate(
                **inputs,
                max_new_tokens=40,
                do_sample=False, 
                num_beams=4,      # Increased beams slightly for better quality
                pad_token_id=tokenizer.eos_token_id if tokenizer.eos_token_id else tokenizer.pad_token_id
            )

        gen = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Post-process: Remove the prompt and initial text echo
        # Using regex to remove the prompt part more robustly
        correction = re.sub(re.escape(prompt), "", gen, 1).strip()
        
        # Aggressive cleaning: find the FIRST complete sentence
        final_correction = ""
        for separator in ['।', '?', '!']:
            if separator in correction:
                final_correction = correction.split(separator)[0] + separator
                break
        
        if not final_correction:
            # If no end punctuation found, use first meaningful fragment (line break or first 10 words)
            final_correction = correction.split('\n')[0].strip()
            if len(final_correction.split()) > 10:
                final_correction = ' '.join(final_correction.split()[:10]) + '।' # Add a period if fragment is long

        # Final cleanup: Remove any residual non-Hindi/non-punctuation characters
        final_correction = re.sub(r'[^ं-ःअ-ह\s\.,!\?।]', '', final_correction).strip()
        final_correction = re.sub(r'\s+', ' ', final_correction).strip()
        
        # Final check for validity
        if not final_correction or len(final_correction.split()) < 2:
            raise ValueError("Corrected text too short/invalid.")
            
        return final_correction.strip()

    except Exception as e:
        print(f"⚠️ Coherence correction failed ({e}). Returning original ASR text.")
        # Fallback to the original ASR text
        return incoherent_text
def conversation_assistant(audio_file: str):
    print(f"\n🎧 Processing audio: {audio_file}")

    # --- Step 1: ASR Transcription + Pronunciation ---
    predicted_text, score = get_pronunciation_score(audio_file)
    print(f"📝 Raw ASR Transcription: {predicted_text}")
    print(f"🔊 Pronunciation Confidence: {score:.2f}/100")

    # --- Step 2: Coherence Correction (Hindi) ---
    coherent_hindi = correct_incoherent_hindi(predicted_text)
    print(f"🧠 Inferred Coherent Hindi: {coherent_hindi}")
    
    # --- Step 3: Translation (using the Coherent Hindi) ---
    english_text = translate_to_english(coherent_hindi) # Translate the *corrected* message
    print(f"🌍 English Translation (Intended Message): {english_text}")

    # --- Step 4: Prosody Analysis & Feedback (using original audio) ---
    prosody = analyze_prosody(audio_file)
    print("\n--- 🎶 Prosody Feedback (For Therapy) ---")
    print(f"Pitch mean: {prosody['pitch_mean']:.2f} Hz")
    print(f"Pitch variance: {prosody['pitch_var']:.2f}")
    print(f"Energy mean: {prosody['energy_mean']:.4f}")
    print(f"Speech rate: {prosody['speech_rate']:.2f} frames/sec") # Corrected unit for clarity

    print("\n💡 Therapy Feedback:")
    for f in prosody['feedback']:
        print(" -", f)
    print("🗣 Suggested Practice Sentence:", prosody['practice_sentence'])
    
    # --- Step 5: Generate Conversational Feedback (Consolidated) ---
    print("\n==============================================")
    print("💬 Conversation Assistant Summary for Caregiver/Therapist:")
    print("==============================================")
    
    print("**Intended Message (for Caregiver):**")
    print(f"   🌍 **English:** '{english_text}'")
    print(f"   🧠 **Hindi:** '{coherent_hindi}'")
    
    print("\n**Therapy and Pronunciation Analysis (for Therapist):**")
    print(f"   📝 **Raw Transcription:** '{predicted_text}'")
    print(f"   🔊 **Confidence Score:** {score:.1f}/100")
    print(f"   🎶 **Prosody Issue:** {prosody['feedback'][0]}")
    print(f"   🗣 **Next Exercise:** '{prosody['practice_sentence']}'")
    print("==============================================")


    return {
        "raw_asr": predicted_text,
        "pron_score": score,
        "coherent_hindi": coherent_hindi,
        "english_translation": english_text,
        "prosody_feedback": prosody.get('feedback', []),
        "practice_sentence": prosody.get('practice_sentence', ''),
        "prosody_metrics": {
            "pitch_mean": prosody.get('pitch_mean'),
            "pitch_var": prosody.get('pitch_var'),
            "energy_mean": prosody.get('energy_mean'),
            "energy_var": prosody.get('energy_var'),
            "speech_rate": prosody.get('speech_rate')
        }
    }
