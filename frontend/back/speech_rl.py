import os
import csv
import time
import numpy as np
from speech_therapy import (
    record_audio, # NOTE: This function is not used in the new design, but imported
    analyze_prosody,
    get_pronunciation_score,
    generate_practice_sentence
)

# =========================
# --- CONFIGURATION ---
# =========================
THRESHOLDS = {
    "pitch_var": 150.0,      
    "energy_mean": 0.03,     
    "speech_rate_min": 2.0,  
    "conf_score": 65.0       
}

WEIGHTS = {
    "pitch_var": 0.25,
    "energy_mean": 0.2,
    "speech_rate": 0.15,
    "conf_score": 0.4
}

LOG_PATH = "therapy_sessions.csv"
TEMP_AUDIO_PATH = "rl_temp_audio.wav"   # Dedicated path for RL recordings

# =========================
# --- REWARD SYSTEM ---
# =========================
def _norm_delta(value, target, higher_better=True):
    if higher_better:
        # Note: Added check to prevent division by zero if target is near zero
        return min(max(value / target, 0.0), 1.0) if target > 1e-8 else 1.0
    else:
        return min(max(target / (value + 1e-8), 0.0), 1.0)


def compute_reward(metrics):
    r_pitch = _norm_delta(metrics["pitch_var"], THRESHOLDS["pitch_var"])
    r_energy = _norm_delta(metrics["energy_mean"], THRESHOLDS["energy_mean"])
    r_rate = _norm_delta(metrics["speech_rate"], THRESHOLDS["speech_rate_min"])
    r_conf = _norm_delta(metrics["conf_score"], THRESHOLDS["conf_score"])

    reward = (
        WEIGHTS["pitch_var"] * r_pitch
        + WEIGHTS["energy_mean"] * r_energy
        + WEIGHTS["speech_rate"] * r_rate
        + WEIGHTS["conf_score"] * r_conf
    )
    return reward


# =========================
# --- LOGGING ---
# =========================
# Keeping this function, but it's not called within therapy_step by default
def log_session(iter_num, metrics, reward):
    file_exists = os.path.isfile(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Iteration", "PitchVar", "EnergyMean", "SpeechRate", "ConfScore", "Reward"])
        writer.writerow([
            iter_num,
            metrics["pitch_var"],
            metrics["energy_mean"],
            metrics["speech_rate"],
            metrics["conf_score"],
            reward
        ])


# =========================
# --- WEAKEST FEATURE ---
# =========================
def weakest_feature(metrics):
    # Check for features below threshold
    deltas = {}
    
    # Use thresholds as a benchmark for weakness
    if metrics["pitch_var"] < THRESHOLDS["pitch_var"]:
        deltas["pitch_var"] = metrics["pitch_var"] / THRESHOLDS["pitch_var"]
    if metrics["energy_mean"] < THRESHOLDS["energy_mean"]:
        deltas["energy_mean"] = metrics["energy_mean"] / THRESHOLDS["energy_mean"]
    if metrics["speech_rate"] < THRESHOLDS["speech_rate_min"]:
        deltas["speech_rate"] = metrics["speech_rate"] / THRESHOLDS["speech_rate_min"]
    if metrics["conf_score"] < THRESHOLDS["conf_score"]:
        deltas["conf_score"] = metrics["conf_score"] / THRESHOLDS["conf_score"]
        
    if deltas:
        # Find the minimum ratio (weakest feature)
        weakest_key = min(deltas, key=deltas.get)
        if weakest_key == "pitch_var": return "pitch"
        if weakest_key == "energy_mean": return "energy"
        if weakest_key == "speech_rate": return "rate"
        return "conf_score"
    
    return "general"


# =========================
# --- RL STEP FUNCTION ---
# =========================
def therapy_step(audio_path, iter_num):
    """
    Performs one step of the RL loop: analyzes the latest audio, computes reward,
    and returns the metrics and the next practice sentence.
    The audio must have been saved to audio_path by the calling API route.
    """
    
    # 1. Analyze the audio sent from the frontend
    transcription, conf_score = get_pronunciation_score(audio_path)
    prosody = analyze_prosody(audio_path)
    
    pitch_var = prosody.get("pitch_var", 0.0)
    energy_mean = prosody.get("energy_mean", 0.0)
    speech_rate = prosody.get("speech_rate", 0.0)
    
    metrics = {
        "pitch_var": pitch_var,
        "energy_mean": energy_mean,
        "speech_rate": speech_rate,
        "conf_score": conf_score
    }
    
    # 2. Compute Reward and Status
    reward = compute_reward(metrics)
    
    is_complete = all([
        metrics["pitch_var"] >= THRESHOLDS["pitch_var"],
        metrics["energy_mean"] >= THRESHOLDS["energy_mean"],
        metrics["speech_rate"] >= THRESHOLDS["speech_rate_min"],
        metrics["conf_score"] >= THRESHOLDS["conf_score"]
    ])
    
    # 3. Determine Next Action
    weakest = weakest_feature(metrics)
    next_practice = generate_practice_sentence(weakest)
    
    # 4. Return results (Frontend handles the loop and logging)
    return {
        "metrics": metrics,
        "reward": reward,
        "next_prompt": next_practice["text"],
        "expected_emotion": next_practice["expected_emotion"],
        "weakest_feature": weakest,
        "is_complete": is_complete
    }