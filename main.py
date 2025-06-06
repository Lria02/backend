from flask import Flask
from flask_cors import CORS

from routes.upload import upload_bp
from routes.reviewer import reviewer_bp
from routes.quiz import quiz_bp

app = Flask(__name__)
CORS(app, origins=["https://lria02.github.io"])

# Register routes
app.register_blueprint(upload_bp, url_prefix='/upload')
app.register_blueprint(reviewer_bp, url_prefix='/reviewer')
app.register_blueprint(quiz_bp, url_prefix='/quiz')

if __name__ == '__main__':
    app.run()
