from app import create_web_app
from app.routes import register_routes

app = create_web_app()
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
