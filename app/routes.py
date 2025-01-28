import os
from flask import render_template, request, redirect, url_for, jsonify
from datetime import datetime
from google.cloud import texttospeech, speech
from werkzeug.utils import secure_filename

def get_client():
    credentials_path = "app/static/json/google_service_account.json"
    return [texttospeech.TextToSpeechClient.from_service_account_file(credentials_path), speech.SpeechClient.from_service_account_file(credentials_path)]

def register_routes(app):
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        generated_files = []
        generated_audio = ""

        # Handle Text-to-Speech
        if request.method == 'POST' and 'text' in request.form:
            text = request.form.get('text')
            if text:
                client = get_client()[0]
                input_text = texttospeech.SynthesisInput(text=text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                response = client.synthesize_speech(
                    input=input_text, voice=voice, audio_config=audio_config
                )

                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"text_to_speech_{timestamp}.wav"
                filepath = os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], filename)
                with open(filepath, "wb") as out:
                    out.write(response.audio_content)

                generated_audio = filename
        generated_files = os.listdir(app.config['UPLOAD_FOLDER_AUDIO'])


        return render_template(
            'index.html',
            audio_files=generated_files,
            generated_audio=generated_audio,
        )
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No file selected for uploading"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER_UPLOADS'], filename)
            file.save(file_path)

            # Transcribe the audio file
            transcript = transcribe_audio(file_path)

            # Clean up the uploaded file
            os.remove(file_path)

            return jsonify({"transcript": transcript})

        return jsonify({"error": "Invalid file type. Only .wav files are allowed."}), 400


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'wav'
    

def transcribe_audio(file_path):
    client = get_client()[1]

    # Read the audio file
    with open(file_path, 'rb') as audio_file:
        content = audio_file.read()

    # Configure the audio and recognition settings
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,  # Update this if your WAV file has a different sample rate
        language_code="en-US"
    )

    # Perform the transcription
    response = client.recognize(config=config, audio=audio)

    # Extract and return the transcript
    transcript = ' '.join(result.alternatives[0].transcript for result in response.results)
    return transcript