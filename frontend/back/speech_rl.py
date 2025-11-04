import os
import csv
import time
import numpy as np
from speech_therapy import (
    record_audio,
    analyze_prosody,
    get_pronunciation_score,
    generate_practice_sentence
)

# =========================
# --- CONFIGURATION ---
# =========================
THRESHOLDS = {
    "pitch_var": 150.0,      # want pitch variance at least this (higher = more intonation)
    "energy_mean": 0.03,     # want energy >= this
    "speech_rate_min": 2.0,  # want speech_rate >= this
    "conf_score": 65.0       # desired ASR confidence (0-100)
}

WEIGHTS = {
    "pitch_var": 0.25,
    "energy_mean": 0.25,
    "speech_rate": 0.25,
    "conf_score": 0.25
}

LOG_PATH = "therapy_sessions.csv"
TEMP_AUDIO_PATH = "temp_audio.wav"   # all recordings use this file


# =========================
# --- REWARD SYSTEM ---
# =========================
def _norm_delta(value, target, higher_better=True):
    if higher_better:
        return min(max(value / target, 0.0), 1.0)
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
# --- RL LOOP ---
# =========================
def weakest_feature(metrics):
    deltas = {
        "pitch_var": metrics["pitch_var"] / THRESHOLDS["pitch_var"],
        "energy_mean": metrics["energy_mean"] / THRESHOLDS["energy_mean"],
        "speech_rate": metrics["speech_rate"] / THRESHOLDS["speech_rate_min"],
        "conf_score": metrics["conf_score"] / THRESHOLDS["conf_score"]
    }
    return min(deltas, key=deltas.get)


def therapy_reinforcement_loop(initial_audio=None, max_iters=5):
    """
    Reinforcement loop for adaptive speech therapy.
    Uses temp_audio.wav for input and overwrites it every round.
    """

    print("\n🎯 Starting Reinforcement-Based Speech Therapy Session...\n")

    # Step 1: Initial analysis
    audio_path = initial_audio or TEMP_AUDIO_PATH
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"{audio_path} not found. Please ensure the initial temp_audio.wav is saved.")

    prosody = analyze_prosody(audio_path)
    pitch_var = prosody.get("pitch_var", 0.0)
    energy_mean = prosody.get("energy_mean", 0.0)
    speech_rate = prosody.get("speech_rate", 0.0)
    conf_score = prosody.get("conf_score", 0.0)

    metrics = {
        "pitch_var": pitch_var,
        "energy_mean": energy_mean,
        "speech_rate": speech_rate,
        "conf_score": conf_score
    }

    history = []
    best_reward = -np.inf

    for i in range(max_iters):
        print(f"\n--- Iteration {i+1} ---")
        print(f"Metrics: {metrics}")

        reward = compute_reward(metrics)
        log_session(i + 1, metrics, reward)
        history.append({"iteration": i + 1, "metrics": metrics.copy(), "reward": reward})

        weakest = weakest_feature(metrics)
        print(f"Weakest feature: {weakest}")

        practice_sentence = generate_practice_sentence(weakest)
        print(f"Next practice sentence: {practice_sentence}")

        print("🗣 Please repeat the above sentence clearly...")

        # Record and overwrite temp_audio.wav
        record_audio(duration=5, output_path=TEMP_AUDIO_PATH)
        print("Analyzing new attempt...")
        prosody = analyze_prosody(audio_path)
        pitch_var = prosody.get("pitch_var", 0.0)
        energy_mean = prosody.get("energy_mean", 0.0)
        speech_rate = prosody.get("speech_rate", 0.0)
        conf_score = prosody.get("conf_score", 0.0)


        metrics = {
            "pitch_var": pitch_var,
            "energy_mean": energy_mean,
            "speech_rate": speech_rate,
            "conf_score": conf_score
        }

        if reward > best_reward:
            best_reward = reward

        # Stop if all thresholds are met
        if all([
            metrics["pitch_var"] >= THRESHOLDS["pitch_var"],
            metrics["energy_mean"] >= THRESHOLDS["energy_mean"],
            metrics["speech_rate"] >= THRESHOLDS["speech_rate_min"],
            metrics["conf_score"] >= THRESHOLDS["conf_score"]
        ]):
            print("\n✅ All thresholds met! Great improvement!")
            break

    print("\n🏁 Session complete.")
    print(f"Best reward achieved: {best_reward:.3f}")

    return metrics, best_reward, history
