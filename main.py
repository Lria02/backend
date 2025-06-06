from flask import Flask
from flask_cors import CORS

from routes.upload import upload_bp
from routes.reviewer import reviewer_bp  # Add this import
from routes.quiz import quiz_bp  # Add this import

# from routes.auth import auth_bp  # Comment this out for now

app = Flask(__name__)
CORS(app)

# Register routes
app.register_blueprint(upload_bp, url_prefix='/upload')
app.register_blueprint(reviewer_bp, url_prefix='/reviewer')  # Register reviewer route
app.register_blueprint(quiz_bp, url_prefix='/quiz')  # Register quiz route
# app.register_blueprint(auth_bp, url_prefix='/auth')  # Comment this out

if __name__ == '__main__':
    app.run()
