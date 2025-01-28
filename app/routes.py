import os
from flask import render_template, request, redirect, url_for, jsonify
from datetime import datetime
from google.cloud import texttospeech, speech

def get_client():
    credentials_path = "app/static/json/google_service_account.json"
    return [texttospeech.TextToSpeechClient.from_service_account_file(credentials_path), speech.SpeechClient.from_service_account_file(credentials_path)]

def register_routes(app):
    
    @app.route('/transcribe', methods=['POST'])
    def transcribe():
        # Save the uploaded audio file
        audio_file = request.files['audio']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        filename = f"speech_to_text_{timestamp}.wav"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER_UPLOADS'], filename)
        audio_file.save(audio_path)

        # Transcribe using Google Speech-to-Text
        client = get_client()[1]

        with open(audio_path, "rb") as audio:
            audio_content = audio.read()

        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US",
        )

        response = client.recognize(config=config, audio=audio)

        # Extract transcript
        transcript = "\n".join(result.alternatives[0].transcript for result in response.results)
        print("Transcript \n", transcript)
        return jsonify({"transcript": transcript, "audio_path": f"/{audio_path}"})
    
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
                filename = f"text_to_speech_{timestamp}.mp3"
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