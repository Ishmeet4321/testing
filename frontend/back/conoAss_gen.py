import os
import re
import torch
import torch.nn.functional as F
import librosa
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import (
    Wav2Vec2Processor,
    Wav2Vec2ForCTC,
    AutoTokenizer,
    AutoModel,
    MarianMTModel,
    MarianTokenizer,
)
from sentence_transformers import SentenceTransformer, util

# -------------------------------
# Load Hindi ASR Model
# -------------------------------
ASR_MODEL = "Harveenchadha/vakyansh-wav2vec2-hindi-him-4200"
processor = Wav2Vec2Processor.from_pretrained(ASR_MODEL)
asr_model = Wav2Vec2ForCTC.from_pretrained(ASR_MODEL)

# -------------------------------
# Load Hindi Embedding Model
# -------------------------------
HINDI_LLM = "ai4bharat/indic-bert"
tok = AutoTokenizer.from_pretrained(HINDI_LLM)
llm_model = AutoModel.from_pretrained(HINDI_LLM)

# -------------------------------
# Translation Models (Hi↔En)
# -------------------------------
hi2en_model = "Helsinki-NLP/opus-mt-hi-en"
en2hi_model = "Helsinki-NLP/opus-mt-en-hi"
hi2en_tok = MarianTokenizer.from_pretrained(hi2en_model)
hi2en_trans = MarianMTModel.from_pretrained(hi2en_model)
en2hi_tok = MarianTokenizer.from_pretrained(en2hi_model)
en2hi_trans = MarianMTModel.from_pretrained(en2hi_model)


# -------------------------------
# Step 1: Transcribe Hindi audio
# -------------------------------
def get_hindi_transcription(audio_path):
    y, sr = librosa.load(audio_path, sr=16000)
    inputs = processor(y, sampling_rate=16000, return_tensors="pt", padding=True)

    with torch.no_grad():
        logits = asr_model(inputs.input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    predicted_text = processor.tokenizer.decode(predicted_ids[0])
    cleaned_text = re.sub(r"<[^>]+>", "", predicted_text).strip()

    # Confidence score
    probs = F.softmax(logits, dim=-1)
    chosen_probs = probs.gather(-1, predicted_ids.unsqueeze(-1)).squeeze(-1)
    conf_score = float(chosen_probs.mean().item()) * 100
    return cleaned_text, conf_score


# -------------------------------
# Step 2: Hindi refinement (placeholder)
# -------------------------------
def semantic_refinement(hindi_text):
    # Later replace with fine-tuned Hindi corrector
    return hindi_text.strip()


# -------------------------------
# Step 3: Translate functions
# -------------------------------
def translate_hi2en(hindi_text):
    if not hindi_text.strip():
        return ""
    inputs = hi2en_tok(hindi_text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = hi2en_trans.generate(**inputs, max_length=512)
    return hi2en_tok.decode(outputs[0], skip_special_tokens=True).strip()


def translate_en2hi(english_text):
    if not english_text.strip():
        return ""
    inputs = en2hi_tok(english_text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = en2hi_trans.generate(**inputs, max_length=512)
    return en2hi_tok.decode(outputs[0], skip_special_tokens=True).strip()


# -------------------------------
# Step 4: Semantic similarity
# -------------------------------
def semantic_similarity(text1, text2):
    with torch.no_grad():
        emb1 = llm_model(**tok(text1, return_tensors="pt", truncation=True, padding=True))[0].mean(dim=1)
        emb2 = llm_model(**tok(text2, return_tensors="pt", truncation=True, padding=True))[0].mean(dim=1)
    sim = cosine_similarity(emb1, emb2)[0][0]
    return float(sim)


# -------------------------------
# Step 5: Combined evaluation
# -------------------------------
def evaluate_transcription(hindi_text, refined_text):
    # Hindi semantic similarity
    sim_hi = semantic_similarity(hindi_text, refined_text)

    # Hindi→English translations
    eng_from_asr = translate_hi2en(hindi_text)
    eng_from_refined = translate_hi2en(refined_text)

    # English semantic similarity
    sim_en = semantic_similarity(eng_from_asr, eng_from_refined)

    # Hindi cycle (Hi→En→Hi)
    back_hi = translate_en2hi(eng_from_asr)
    cyc_hi = semantic_similarity(hindi_text, back_hi)

    # English cycle (En→Hi→En)
    back_en = translate_hi2en(refined_text)
    cyc_en = semantic_similarity(eng_from_asr, back_en)

    # Combined bilingual metrics
    bilingual_sim = 0.5 * (sim_hi + sim_en)
    bilingual_cyc = 0.5 * (cyc_hi + cyc_en)

    return {
        "eng_from_asr": eng_from_asr,
        "eng_from_refined": eng_from_refined,
        "sim_hi": sim_hi,
        "sim_en": sim_en,
        "cyc_hi": cyc_hi,
        "cyc_en": cyc_en,
        "bilingual_sim": bilingual_sim,
        "bilingual_cyc": bilingual_cyc,
    }


# -------------------------------
# Step 6: Example usage
# -------------------------------
if __name__ == "__main__":
    audio_file_path = "generated_audio/slurred.wav"

    if not os.path.exists(audio_file_path):
        print("❌ Audio file not found! Please check the path.")
    else:
        # Step 1: Transcription
        hindi_text, score = get_hindi_transcription(audio_file_path)

        # Step 2: Hindi refinement
        refined_hindi = semantic_refinement(hindi_text)

        # Step 3: Evaluate
        metrics = evaluate_transcription(hindi_text, refined_hindi)

        # -------------------------------
        # Display Results
        # -------------------------------
        print(f"\nTranscribed Hindi: {hindi_text}")
        print(f"Pronunciation Confidence: {score:.2f}")
        print(f"Refined Hindi Output: {refined_hindi}")
        print(f"English (ASR): {metrics['eng_from_asr']}")
        print(f"English (Refined): {metrics['eng_from_refined']}")
        print(f"Semantic Similarity (Hindi): {metrics['sim_hi']:.4f}")
        print(f"Semantic Similarity (English): {metrics['sim_en']:.4f}")
        print(f"Cycle Consistency (Hindi→Eng→Hi): {metrics['cyc_hi']:.4f}")
        print(f"Cycle Consistency (Eng→Hi→Eng): {metrics['cyc_en']:.4f}")
        print(f"Final Bilingual Semantic Score: {metrics['bilingual_sim']:.4f}")
        print(f"Final Bilingual Cycle Score: {metrics['bilingual_cyc']:.4f}")
