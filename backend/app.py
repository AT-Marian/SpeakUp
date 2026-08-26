from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"\n{'='*70}")
print(f"🔧 APP INITIALIZATION")
print(f"Backend Directory: {BACKEND_DIR}")
print(f"{'='*70}\n")

# Load .env file
env_path = os.path.join(BACKEND_DIR, '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Set Google Cloud credentials
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if credentials_path:
    if not os.path.isabs(credentials_path):
        full_credentials_path = os.path.join(BACKEND_DIR, credentials_path)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = full_credentials_path
        print(f"✓ Using credentials: {full_credentials_path}")
    else:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        print(f"✓ Using credentials: {credentials_path}")
else:
    print(f"⚠️  No GOOGLE_APPLICATION_CREDENTIALS in .env")

# Verify credentials file exists
creds_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
if creds_file and os.path.exists(creds_file):
    print(f"✓ Google credentials file found")
else:
    print(f"⚠️  Google credentials file NOT found")

print(f"GOOGLE_CLOUD_PROJECT = {os.getenv('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")
print(f"{'='*70}\n")

# Import route blueprints
from routes import auth, practice, users
from utils.helpers import generate_response, Logger

# Create Flask app
app = Flask(__name__)

# Normalize multiple slashes in request paths (e.g. //api -> /api)
class NormalizeSlashMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '')
        if '//' in path_info:
            import re
            environ['PATH_INFO'] = re.sub(r'/+', '/', path_info)
        return self.app(environ, start_response)

app.wsgi_app = NormalizeSlashMiddleware(app.wsgi_app)

# Load configuration from config.py
from config import config
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
jwt = JWTManager(app)
cors_origins = app.config.get('CORS_ORIGINS', '*')
CORS(app, resources={r"/*": {"origins": cors_origins}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    from flask import request
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    elif cors_origins == '*':
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

# --- DATABASE CONNECTION ---
MONGO_URI = os.getenv('MONGODB_URI', "mongodb+srv://AT-Marian:Tm200114@cluster0.bibltvc.mongodb.net/speakup?retryWrites=true&w=majority&authSource=admin")
DB_NAME = os.getenv('DATABASE_NAME', "speakup")

try:
    mongo_client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
    db = mongo_client[DB_NAME]
    
    # Verify connection
    mongo_client.admin.command('ping')
    print("✅ Flask App: Connected to MongoDB successfully")
    Logger.info(f"Connected to MongoDB: {DB_NAME}")
except Exception as e:
    print(f"❌ Flask App: Database connection failed: {e}")
    Logger.error(f"MongoDB connection failed: {str(e)}")
    db = None

# --- ROUTE SETUP ---
if db is not None:
    auth.set_database(db)
    practice.set_database(db)
    users.set_database(db)

# Register blueprints
app.register_blueprint(auth.auth_bp)
app.register_blueprint(practice.practice_bp)
app.register_blueprint(users.users_bp)

# --- ERROR HANDLERS & ROUTES ---
@app.errorhandler(404)
def not_found(error):
    return generate_response(False, 'Resource not found', None, 404)

@app.route('/health', methods=['GET'])
def health_check():
    return generate_response(True, 'Server is healthy', {'status': 'ok'}, 200)

@app.route('/', methods=['GET'])
def root():
    return generate_response(True, 'SpeakUp API', {'version': '1.0.0'}, 200)

if __name__ == '__main__':
    port = int(app.config.get('PORT', 5000))
    host = app.config.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=app.config.get('DEBUG', True), use_reloader=False)