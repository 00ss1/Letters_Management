import os
from bson import ObjectId
from flask import Flask, redirect, url_for, session, request, jsonify
from authlib.integrations.flask_client import OAuth
from pymongo import MongoClient
from flask_session import Session
from flask_cors import CORS
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
import traceback
import secrets
import requests
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID_WEB")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET_WEB")

print(f"Loaded Client ID: {GOOGLE_CLIENT_ID}")  # Debugging (remove in production)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    raise FileNotFoundError(".env file not found in the backend directory")

app = Flask(__name__)
CORS(app,supports_credentials=True)
app.secret_key = os.urandom(24)
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in the .env file")
client = MongoClient(MONGO_URI)
db = client["LetterEditorProject"]
users_collection = db["users"]
letters_collection = db["letters"]
bcrypt = Bcrypt(app)

@app.route("/")
def index():
    user = session.get("user")
    if user:
        return f"Welcome {user['name']}! <br><a href='/logout'>Logout</a>"
    else:
        return "Welcome to Google OAuth with Flask! <br><a href='/login'>Login with Google</a> <br> Flask backend is running with MongoDB!"

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"message": "Missing username, password, or email"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"message": "Username or email already exists"}), 400

    try:
        users_collection.insert_one({"username": username, "password": hashed_password, "email": email})
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"message": f"Database error: {e}"}), 500

@app.route("/basic-login", methods=["POST"])
def basic_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 400

    user = users_collection.find_one({"username": username})

    if user and bcrypt.check_password_hash(user["password"], password):
        session["username"] = username
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401

@app.route("/basic-logout")
def basic_logout():
    session.pop("username", None)
    return jsonify({"message": "Logout successful"}), 200

@app.route("/store-user", methods=["POST"])
def store_user():
    data = request.json
    existing_user = users_collection.find_one({"email": data["email"]})
    if not existing_user:
        users_collection.insert_one({
            "name": data["name"],
            "email": data["email"],
            "google_id": data["google_id"]
        })
    return jsonify({"message": "User stored successfully"}), 201

# Letter routes (ADD THEM HERE)
@app.route("/save-letter", methods=["POST"])
def save_letter():
    data = request.json
    letters_collection.insert_one({
        "user_email": data["email"],
        "title": data["title"],
        "content": data["content"]
    })
    return jsonify({"message": "Letter saved successfully"}), 201

@app.route("/get-letters/<email>", methods=["GET"])
def get_letters(email):
    letters = list(letters_collection.find({"user_email": email}))
    for letter in letters:
        letter["_id"] = str(letter["_id"])
    return jsonify(letters), 200

@app.route("/update-letter/<letter_id>", methods=["PUT"])
def update_letter(letter_id):
    data = request.json
    try:
        result = letters_collection.update_one(
            {"_id": ObjectId(letter_id)},
            {"$set": {"title": data["title"], "content": data["content"]}}
        )
        if result.modified_count > 0:
            return jsonify({"message": "Letter updated successfully"}), 200
        else:
            return jsonify({"message": "Letter not found"}), 404
    except Exception as e:
        return jsonify({"message": "Invalid letter ID"}), 400

@app.route("/delete-letter/<letter_id>", methods=["DELETE"])
def delete_letter(letter_id):
    try:
        result = letters_collection.delete_one({"_id": ObjectId(letter_id)})
        if result.deleted_count > 0:
            return jsonify({"message": "Letter deleted successfully"}), 200
        else:
            return jsonify({"message": "Letter not found"}), 404
    except Exception as e:
        return jsonify({"message": "Invalid letter ID"}), 400

@app.route("/get-letter/<letter_id>", methods=["GET"])
def get_letter(letter_id):
    try:
        letter = letters_collection.find_one({"_id": ObjectId(letter_id)})
        if letter:
            letter["_id"] = str(letter["_id"])
            return jsonify(letter), 200
        else:
            return jsonify({"message": "Letter not found"}), 404
    except Exception as e:
        return jsonify({"message": "Invalid letter ID"}), 400

SCOPES = ["https://www.googleapis.com/auth/drive"]

@app.route("/save-to-drive", methods=["POST"])
def save_to_drive():
    data = request.json
    email = data["email"]
    title = data["title"]
    content = data["content"]

    creds = None
    if os.path.exists(f'token_{email}.pickle'):
        with open(f'token_{email}.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES, redirect_uri="http://localhost"
        )
        creds = flow.run_local_server(port=0)
        with open(f'token_{email}.pickle', 'wb') as token:
            pickle.dump(creds, token)

    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)

    file_metadata = {'name': title, 'mimeType': 'application/vnd.google-apps.document'}
    file = drive_service.files().create(body=file_metadata, fields='id, webViewLink').execute()
    document_id = file.get('id')
    document_link = file.get('webViewLink')

    requests_body = {
        'requests': [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': content,
                },
            },
        ],
    }

    docs_service.documents().batchUpdate(documentId=document_id, body=requests_body).execute()

    return jsonify({"message": "Letter saved to Google Drive", "document_id": document_id, "document_link": document_link}), 200

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.route("/google-login") # Renamed to avoid conflict with basic login
def google_login():
    session['nonce'] = secrets.token_urlsafe(32)
    return google.authorize_redirect("http://127.0.0.1:5000/login/authorized", nonce=session['nonce'])

@app.route("/google-logout") # Renamed to avoid conflict with basic logout
def google_logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/login/authorized")
def authorized():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=session['nonce'])
        session["user"] = user_info
        del session['nonce']
        user_data = {
            "name": user_info["name"],
            "email": user_info["email"],
            "google_id": user_info["sub"]
        }
        response = requests.post("http://127.0.0.1:5000/store-user", json=user_data)
        print("Store user response:", response.json(), response.status_code)
        return redirect(url_for("index"))
    except Exception as e:
        print("🔴 ERROR during authorization:")
        traceback.print_exc()
        return "Authorization failed. Please check the server logs.", 500

@app.route("/profile")
def profile():
    user = session.get("user")
    if not user:
        return redirect(url_for("google_login"))  # Redirect to Google login
    return jsonify(user)   
