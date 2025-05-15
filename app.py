from flask import Flask, request, jsonify, Response, send_file
import time
import threading
import wave
import os
from datetime import datetime
import cloudinary.uploader
import tempfile
import requests
import re
from huggingface_hub import InferenceClient
from gtts import gTTS

app = Flask(__name__)

AUDIO_FOLDER = "recordings"
SAVE_DIR = "received_images"
ANSWERS_DIR = "beats"  # New folder for saving audio answers
SAMPLE_RATE = 16000
CHUNK_SIZE = 0  # No limit from ESP
BUFFER = bytearray()
BUFFER_LOCK = threading.Lock()
LAST_SAVE_TIME = time.time()
LATEST_AUDIO_CHUNK = None  # Track the latest audio chunk filename

# Cloudinary configuration
CLOUDINARY_API_KEY = "532718876252765"
CLOUDINARY_API_SECRET = "8xIh7tTVV_VsW_996YltNBdEG8Q"
CLOUDINARY_CLOUD_NAME = "du54acioe"

# Groq API Key
groq_api_key = "your grok api key"

# Hugging Face Inference Client configuration
client = InferenceClient(
    provider="fal-ai",
    api_key="your hugging face api key(optional)",
)

# Ensure folders exist
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(ANSWERS_DIR, exist_ok=True)  # Ensure the answers folder exists

def text_to_speech(text: str) -> bytes:
    """
    Converts text to speech using gTTS.
    """
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        mp3_bytes = f.read()
    os.remove("temp.mp3")
    return mp3_bytes

def save_wav(data, index):
    global LATEST_AUDIO_CHUNK
    filename = os.path.join(AUDIO_FOLDER, f"chunk_{index}.wav")
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(data)
    print(f"Saved: {filename} ({len(data)} bytes)")
    LATEST_AUDIO_CHUNK = filename  # Update the latest audio chunk filename
    return filename

def background_saver():
    global BUFFER, LAST_SAVE_TIME
    index = 0
    while True:
        time.sleep(1)
        with BUFFER_LOCK:
            if len(BUFFER) >= SAMPLE_RATE * 2 * 10:  # 10 seconds * 16-bit * 1 channel
                chunk = BUFFER[:SAMPLE_RATE * 2 * 10]
                BUFFER = BUFFER[SAMPLE_RATE * 2 * 10:]
                wav_filename = save_wav(chunk, index)
                index += 1
                # Analyze the latest image with the new audio chunk
                analyze_latest_image_with_audio(wav_filename)

def analyze_latest_image_with_audio(audio_file_path):
    latest_image_path = os.path.join(SAVE_DIR, "latest_image.jpg")
    if os.path.exists(latest_image_path):
        image_url = upload_image_to_cloudinary(latest_image_path)
        context = generate_image_context_grok(image_url)
        translated_question = translate_audio(audio_file_path)
        final_answer = answer_user_question(context, translated_question)
        print(f"Final Answer: {final_answer}")

def upload_image_to_cloudinary(file_path):
    upload_result = cloudinary.uploader.upload(
        file_path,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        cloud_name=CLOUDINARY_CLOUD_NAME,
        public_id="image_as_jpg",
        fetch_format="jpg",
    )
    return upload_result["secure_url"]

def generate_image_context_grok(
    image_url: str,
    model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
    temperature: float = 1.0,
    max_completion_tokens: int = 1024,
) -> str:
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "This is a live photo taken. Please analyze the image "
                        "and provide a structured response without making unsupported assumptions.\n\n"
                        "Response format:\n"
                        "1. Overall Description (3 paragraphs)\n"
                        "2. Objects (each object described in 2 paragraphs)"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
            ],
        }
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
    }

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
    )

    if resp.status_code != 200:
        print("=== Groq API Error ===")
        print("Status code:", resp.status_code)
        print("Body:", resp.text)
        resp.raise_for_status()

    data = resp.json()
    raw_input_str = str(data["choices"][0]["message"]["content"])

    match = re.search(r"content=\"(.*?)\"", raw_input_str, re.DOTALL)
    if match:
        context = match.group(1)
    else:
        context = raw_input_str.strip()

    return context

def answer_user_question(context, user_question):
    prompt = (
        f"Context:\n{context}\n\n"
        f"Question:\n{user_question}\n\n"
        "Please provide a conversational answer and be friendly. Do not include any additional commentary, explanations, or headings."
    )
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_completion_tokens": 500,
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def translate_audio(
    audio_file_path: str,
    model: str = "whisper-large-v3",
    response_format: str = "text",
) -> str:
    with open(audio_file_path, "rb") as f:
        files = {"file": f}
        data = {
            "model": model,
            "response_format": response_format,
            "temperature": 0.0,
            "language": "en",
        }   
        headers = {"Authorization": f"Bearer {groq_api_key}"}

        resp = requests.post(
            "https://api.groq.com/openai/v1/audio/translations",
            headers=headers,
            files=files,
            data=data,
        )
        resp.raise_for_status()
        return resp.text.strip()

@app.route('/stream', methods=['POST'])
def stream():
    global BUFFER
    data = request.data
    with BUFFER_LOCK:
        BUFFER += data
    return "OK", 200

@app.route('/', methods=['POST'])
def receive_image():
    if request.data:
        image_filename = os.path.join(SAVE_DIR, "latest_image.jpg")
        with open(image_filename, 'wb') as f:
            f.write(request.data)
        return f"Image received and saved as {image_filename}", 200
    else:
        return "No image received", 400

@app.route("/analyze_image", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    img = request.files["image"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        img.save(tmp.name)
        local_path = tmp.name

    image_url = upload_image_to_cloudinary(local_path)
    context = generate_image_context_grok(image_url)

    return jsonify({"context": context})

@app.route("/ask_question", methods=["POST"])
def ask_question():
    context = request.form.get("context")
    if not context:
        return jsonify({"error": "No context provided"}), 400

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio.save(tmp.name)
        audio_path = tmp.name

    translated_question = translate_audio(audio_path)

    print(f"Requesting answer for question: {translated_question}")
    final_answer = answer_user_question(context, translated_question)
    
    print(f"Final Answer: {final_answer}")
    print(f"Type of final_answer: {type(final_answer)}")
    print(f"Content of final_answer: {final_answer}")

    # Ensure final_answer is a string
    if not isinstance(final_answer, str):
        final_answer = str(final_answer)

    # Save the final answer to a file
    try:
        with open("final_answer.txt", "w") as f:
            f.write(final_answer)
        print("Final answer saved to final_answer.txt")
    except Exception as e:
        print(f"Error writing final answer to file: {e}")

    # Convert final answer to speech
    try:
        mp3_bytes = text_to_speech(final_answer)
        print(f"Generated audio bytes: {len(mp3_bytes)}")
    except Exception as e:
        print(f"Error converting text to speech: {e}")
        return jsonify({"error": "Failed to convert text to speech"}), 500

    # Save the audio response to the ANSWERS_DIR
    try:
        index = len(os.listdir(ANSWERS_DIR))
        audio_filename = os.path.join(ANSWERS_DIR, f"answer_{index}.mp3")
        with open(audio_filename, 'wb') as f:
            f.write(mp3_bytes)
        print(f"Saved audio file: {audio_filename}")
    except Exception as e:
        print(f"Error saving audio file: {e}")
        return jsonify({"error": "Failed to save audio file"}), 500

    return jsonify({"message": f"Audio file saved as {audio_filename}"}), 200
@app.route("/")
def home():
    return "Welcome to NavigAid!"

if __name__ == '__main__':
    threading.Thread(target=background_saver, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
