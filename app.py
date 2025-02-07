import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import bcrypt
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
firebase_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not firebase_key_path or not os.path.exists(firebase_key_path):
    raise FileNotFoundError(f"Firebase credentials file not found at {firebase_key_path}")


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load Firebase credentials securely


cred = credentials.Certificate(firebase_key_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'certificatelocker-a8584.appspot.com'  # Ensure this is your correct bucket name
})

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpeg', 'jpg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB file size limit

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ensure the database folder exists
if not os.path.exists('database'):
    os.makedirs('database')

# Database file path
DATABASE = os.path.join('database', 'certificates.db')

# Initialize the database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create certificates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

# Initialize the database
init_db()

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch user from the database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

# Route for the sign-up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user into the database
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password.decode('utf-8')))
                conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered. Please use a different email.', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

# Route for the upload page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('Please login to upload certificates.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        certificate_name = request.form.get('certificateName')
        certificate_file = request.files.get('certificateFile')

        # Validate file
        if not certificate_file or certificate_file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('upload'))

        if not allowed_file(certificate_file.filename):
            flash('Invalid file type. Allowed formats: PDF, PNG, JPEG.', 'error')
            return redirect(url_for('upload'))

        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f"certificates/{session['user_id']}/{certificate_file.filename}")
        blob.upload_from_file(certificate_file)
        blob.make_public()  # Make the file publicly accessible (optional)

        # Save certificate metadata to the database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO certificates (user_id, name, file_path)
                VALUES (?, ?, ?)
        ''', (session['user_id'], certificate_name, blob.public_url))
        conn.commit()  # Ensure changes are saved


        flash('Certificate uploaded successfully!', 'success')
        return redirect(url_for('upload'))

    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to view your dashboard.', 'error')
        return redirect(url_for('login'))

    # Fetch user's certificates from the database
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM certificates WHERE user_id = ?', (session['user_id'],))
        certificates = cursor.fetchall()

    return render_template('dashboard.html', certificates=certificates)

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)