from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt
import datetime
from flask_cors import CORS
from convo_assist import translate_to_english, translate_to_hindi
import numpy as np # Import numpy once at the top for cleaner code

import convo_assist
import speech_therapy
import transcription
import emotion_analysis
import translation
import video_processing
import audio_preproc
import speech_rl

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'change_this_to_a_random_secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    db.session.add(User(username=username, password=hashed))
    db.session.commit()
    return jsonify({'message': 'User created'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        token = jwt.encode({
            'username': username, 
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Missing token'}), 403
    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        return jsonify({'message': f'Welcome {decoded["username"]}!'})
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

# Helper function to convert numpy types to Python native types
def convert_to_python_types(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_python_types(x) for x in obj]
    else:
        return obj

@app.route('/api/speechtherapy', methods=['POST'])
def api_speech_therapy():
    audio_file = request.files['audio']
    # NEW: Get the image file
    image_file = request.files.get('image')
    
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)
    
    # NEW: Analyze emotion from the image
    detected_emotion = "neutral"
    if image_file:
        image_path = "temp_image.jpg"
        image_file.save(image_path)
        # Use your existing emotion_analysis function
        detected_emotion = emotion_analysis.analyze_emotion(image_path)

    transcription_text, score = speech_therapy.get_pronunciation_score(audio_path)
    prosody = speech_therapy.analyze_prosody(audio_path)

    # Convert score to native float
    try:
        score_py = float(score)
    except Exception:
        score_py = float(score.item()) if hasattr(score, 'item') else float(score)

    # Recursively ensure ALL prosody numerical values/lists are Python types
    prosody_py = convert_to_python_types(prosody)

    # NEW: Add emotion feedback logic
    feedback_list = prosody_py.get("feedback", [])
    expected_emotion = request.form.get("expected_emotion") # Get expected emotion from frontend form data

    if expected_emotion and expected_emotion.lower() != detected_emotion.lower():
        feedback_list.append(f"⚠️ Your facial expression was **{detected_emotion.capitalize()}**, but the sentence required a **{expected_emotion.capitalize()}** expression. Try matching your emotion to the text!")
        # If emotion mismatch is critical, suggest working on it
        if prosody_py.get("target_area", "general") == "general":
             prosody_py["target_area"] = "emotion"

    return jsonify({
        "transcription": transcription_text,
        "score": score_py,
        "pronunciation_score": score_py,
        "feedback": feedback_list, # Use the new list
        "detected_emotion": detected_emotion, # NEW
        "target_area": prosody_py.get("target_area", "general")
    })

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    prompt = data.get("prompt", "general")
    lang = data.get("lang", "hi")
    
    try:
        # CHANGED: Handle the new dictionary response from generate_practice_sentence
        result = speech_therapy.generate_practice_sentence(prompt)
        generated_text = result["text"]
        expected_emotion = result["expected_emotion"]
        
        return jsonify({
            "text": generated_text,
            "lang": lang,
            "prompt": prompt,
            "expected_emotion": expected_emotion # NEW: Return expected emotion
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

@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    audio_file = request.files['audio']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)
    
    prosody = speech_therapy.analyze_prosody(audio_path)
    
    # Convert numpy types to Python types
    prosody_py = convert_to_python_types(prosody)
    
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

    return jsonify({
        "transcription": transcription_text,
        "score": score_py,
        "pronunciation_score": score_py,
        "translation_en": english_text,
        "back_hindi": back_to_hindi,
    })


@app.route('/api/therapy_step', methods=['POST'])
def api_therapy_step():
    """
    Performs one non-blocking step of the RL loop, driven by the frontend.
    Requires audio and iteration number from the client.
    """
    audio_file = request.files.get('audio')
    iter_num_str = request.form.get("iteration")
    
    if not audio_file or not iter_num_str:
        return jsonify({"status": "error", "message": "Missing audio file or iteration number."}), 400

    try:
        audio_path = "rl_temp_audio.wav" # Use a dedicated audio path
        audio_file.save(audio_path)
        iter_num = int(iter_num_str)

        step_result = speech_rl.therapy_step(audio_path, iter_num)
        
        # Convert NumPy types for safe JSON serialization
        metrics_py = convert_to_python_types(step_result["metrics"])

        return jsonify({
            "status": "success",
            "iteration": iter_num,
            "metrics": metrics_py,
            "reward": float(step_result["reward"]),
            #"feedback":step_result["feedback"],
            "next_prompt": step_result["next_prompt"],
            "expected_emotion": step_result["expected_emotion"],
            "weakest_feature": step_result["weakest_feature"],
            "is_complete": step_result["is_complete"]
        })
    except Exception as e:
        import traceback
        print("❌ ERROR in /api/therapy_step:")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
