import os
from flask import render_template, request, redirect, url_for
from datetime import datetime
from google.cloud import texttospeech, speech

def get_client():
    # Provide the path to your service account JSON file
    credentials_path = "app/static/json/google_service_account.json"
    return [texttospeech.TextToSpeechClient.from_service_account_file(credentials_path), speech.SpeechClient.from_service_account_file(credentials_path)]

def register_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        generated_files = []
        transcription_files = []

        # Text-to-Speech logic
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
                response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)

                # Save the generated audio
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"text_to_speech_{timestamp}.mp3"
                filepath = os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], filename)
                with open(filepath, "wb") as out:
                    out.write(response.audio_content)

        # Speech-to-Text logic (Processing recorded audio)
        if request.method == 'POST' and 'audio_data' in request.files:
            audio_file = request.files['audio_data']
            if audio_file:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                original_filename = f"uploaded_{timestamp}.wav"
                upload_path = os.path.join(app.config['UPLOAD_FOLDER_UPLOADS'], original_filename)

                # Save uploaded file
                audio_file.save(upload_path)

                # Use Google Speech-to-Text API
                client = get_client()[1]
                with open(upload_path, "rb") as audio_file_data:
                    audio_content = audio_file_data.read()

                audio = speech.RecognitionAudio(content=audio_content)
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US"
                )

                try:
                    response = client.recognize(config=config, audio=audio)
                    if response.results:
                        transcriptions = [result.alternatives[0].transcript for result in response.results]
                        transcription_filename = f"transcription_{timestamp}.txt"
                        transcription_path = os.path.join(app.config['UPLOAD_FOLDER_AUDIO'], transcription_filename)

                        with open(transcription_path, "w") as transcription_file:
                            transcription_file.write("\n".join(transcriptions))

                        # Add transcription filename to list for rendering
                        transcription_files.append(transcription_filename)
                    else:
                        print("No transcription results found.")
                except Exception as e:
                    print(f"Error during transcription: {e}")

        # Fetch existing audio and transcription files
        generated_files = os.listdir(app.config['UPLOAD_FOLDER_AUDIO'])
        transcription_files = [
            f for f in generated_files if f.endswith(".txt")
        ]

        return render_template(
            'index.html',
            audio_files=generated_files,
            transcription_files=transcription_files,
        )