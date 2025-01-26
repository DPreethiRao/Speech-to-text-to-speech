from flask import Flask

def create_web_app():
    web_app = Flask(__name__)
    web_app.config['SECRET_KEY'] = 'your-secret-key'
    web_app.config['UPLOAD_FOLDER_AUDIO'] = 'app/static/audio'
    web_app.config['UPLOAD_FOLDER_UPLOADS'] = 'app/static/uploads'
    return web_app
