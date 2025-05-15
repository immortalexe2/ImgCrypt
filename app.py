from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
import os

# Initialize the Flask web application
app = Flask(__name__)

# Define folders for handling different file types
UPLOAD_FOLDER = 'uploads'         # Stores original uploaded files
ENCRYPTED_FOLDER = 'encrypted'    # Stores encrypted files
DECRYPTED_FOLDER = 'decrypted'    # Stores decrypted output files

# Configure these folders in the app settings
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ENCRYPTED_FOLDER'] = ENCRYPTED_FOLDER
app.config['DECRYPTED_FOLDER'] = DECRYPTED_FOLDER

# Generate a symmetric encryption key (same key used for encrypting and decrypting)
# NOTE: In production, store this key securely (e.g., environment variable or key vault)
key = Fernet.generate_key()
fernet = Fernet(key)

# Route to the homepage
@app.route('/')
def index():
    return render_template('index.html')  # Loads the main HTML page


# Route to handle image encryption
@app.route('/encrypt', methods=['POST'])
def encrypt_image():
    file = request.files['file']  # Get the uploaded file
    if file.filename == '':
        return 'No file selected'  # Return error if no file is uploaded

    filename = secure_filename(file.filename)  # Sanitize the filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)  # Save the uploaded file to the upload folder

    # Read the contents of the original file
    with open(file_path, 'rb') as f:
        original = f.read()

    # Encrypt the content using Fernet
    encrypted = fernet.encrypt(original)

    base_name, ext = os.path.splitext(filename)

    # Save the encrypted content to a new file
    encrypted_file_name = f'enc_{base_name}.enc'
    encrypted_path = os.path.join(ENCRYPTED_FOLDER, encrypted_file_name)
    with open(encrypted_path, 'wb') as ef:
        ef.write(encrypted)

    # Save the original file extension in a separate file
    with open(os.path.join(ENCRYPTED_FOLDER, f'enc_{base_name}.ext'), 'w') as ext_file:
        ext_file.write(ext)

    # Reload the homepage with a download link for the encrypted file
    return render_template('index.html', encrypted_file=encrypted_file_name)


# Route to handle image decryption
@app.route('/decrypt', methods=['POST'])
def decrypt_image():
    file = request.files['file']  # Get the encrypted file
    if file.filename == '':
        return 'No file selected'  # Error handling if no file provided

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['ENCRYPTED_FOLDER'], filename)
    file.save(file_path)  # Save encrypted file temporarily for reading

    base_name = os.path.splitext(filename)[0]  # Remove extension from filename

    # Read encrypted content from file
    with open(file_path, 'rb') as f:
        encrypted = f.read()

    # Load the original file extension
    with open(os.path.join(ENCRYPTED_FOLDER, f'{base_name}.ext'), 'r') as ext_file:
        original_ext = ext_file.read().strip()

    # Decrypt the content using the same Fernet key
    decrypted = fernet.decrypt(encrypted)

    # Save the decrypted data back to a file with the original extension
    output_filename = f'dec_{base_name}{original_ext}'
    output_path = os.path.join(DECRYPTED_FOLDER, output_filename)
    with open(output_path, 'wb') as df:
        df.write(decrypted)

    # Reload the homepage with a download link for the decrypted file
    return render_template('index.html', decrypted_file=output_filename)


# Route to handle file downloads
@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    # Send the requested file from the given folder as a download
    return send_from_directory(folder, filename, as_attachment=True)


# Main block: Create required folders and run the Flask app
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
    os.makedirs(DECRYPTED_FOLDER, exist_ok=True)
    app.run(debug=True)  # Run the app in debug mode for development
