from flask import Flask, request, jsonify
from flask_cors import CORS
from convo_assist import translate_to_english, translate_to_hindi

import convo_assist
import speech_therapy
import transcription
import emotion_analysis
import translation
import video_processing
import audio_preproc

app = Flask(__name__)
CORS(app)

@app.route('/api/speechtherapy', methods=['POST'])
def api_speech_therapy():
    audio_file = request.files['audio']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)
    transcription_text, score = speech_therapy.get_pronunciation_score(audio_path)
    prosody = speech_therapy.analyze_prosody(audio_path)

    # Convert score to native float
    try:
        score_py = float(score)
    except Exception:
        score_py = float(score.item()) if hasattr(score, 'item') else float(score)

    # Recursively ensure ALL prosody numerical values/lists are Python types
    import numpy as np
    def convert(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(x) for x in obj]
        else:
            return obj

    prosody_py = convert(prosody)

    return jsonify({
        "transcription": transcription_text,
        "score": score_py,
        "pronunciation_score": score_py,
        "feedback": prosody_py.get("feedback", [])
    })

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    prompt = data.get("prompt", "general")  # feature type: 'pitch', 'energy', 'rate', or 'general'
    lang = data.get("lang", "hi")  # language: 'hi' or 'en'
    
    try:
        # Call the Lingo-based function from speech_therapy module
        generated_text = speech_therapy.generate_practice_sentence(prompt)
        
        return jsonify({
            "text": generated_text,
            "lang": lang,
            "prompt": prompt
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    audio_file = request.files['audio']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)
    transcription_text = transcription.transcribe_audio(audio_path)
    return jsonify({"transcription": transcription_text})

@app.route('/api/emotion', methods=['POST'])
def api_emotion():
    image_file = request.files['image']
    image_path = "temp_image.jpg"
    image_file.save(image_path)
    emotion_result = emotion_analysis.analyze_emotion(image_path)
    return jsonify({"emotion": emotion_result})

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.get_json()
    hindi_text = data.get("hindi", "")
    translation_text = translation.translate_hindi_to_english(hindi_text)
    return jsonify({"translation": translation_text})

@app.route('/api/videolandmark', methods=['POST'])
def api_video_landmarks():
    video_file = request.files['video']
    video_path = "temp_video.mp4"
    video_file.save(video_path)
    landmarks = video_processing.analyze_landmarks(video_path)
    # landmarks may need to be serialized further for JSON
    return jsonify({"landmarks": str(landmarks)})

@app.route('/api/audiopreproc', methods=['POST'])
def api_audio_preproc():
    audio_file = request.files['audio']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)
    feat = audio_preproc.extract_audio_features(audio_path)
    return jsonify({"features": feat})

if __name__ == '__main__':
    app.run(port=5000, debug=True)

@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    audio_file = request.files['audio']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)
    
    prosody = speech_therapy.analyze_prosody(audio_path)
    
    # Convert numpy types to Python types
    import numpy as np
    def convert(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(x) for x in obj]
        else:
            return obj
    
    prosody_py = convert(prosody)
    
    return jsonify({
        "feedback": prosody_py.get("feedback", []),
        "target_area": prosody_py.get("target_area", "general"),
        "pronunciation_score": 0
    })

@app.route('/api/convo_assist', methods=['POST'])
def api_convo_assist():
    audio_file = request.files['audio']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)

    transcription_text, score = convo_assist.get_pronunciation_score(audio_path)
    english_text = convo_assist.translate_to_english(transcription_text)
    back_to_hindi = convo_assist.translate_to_hindi(english_text)

    # Convert score to native float
    try:
        score_py = float(score)
    except Exception:
        score_py = float(score.item()) if hasattr(score, 'item') else float(score)

    # Recursively ensure ALL prosody numerical values/lists are Python types
    import numpy as np
    def convert(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(x) for x in obj]
        else:
            return obj

    return jsonify({
        "transcription": transcription_text,
        "score": score_py,
        "pronunciation_score": score_py,
        "translation_en": english_text,
        "back_hindi": back_to_hindi,
    })