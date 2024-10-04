from flask import Flask, jsonify, render_template
import requests
import pyotp
import time

app = Flask(__name__)

# Configuration: Replace with actual registered website name and secret
WEBSITE_NAME = "www.cg.com"  # Replace with your registered website name
AUTHENTICATOR_SERVER_URL = "http://127.0.0.1:5000"  # Adjust if different

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-code', methods=['GET'])
def get_code():
    # Fetch the secret from the Authenticator Server
    response = requests.get(f"{AUTHENTICATOR_SERVER_URL}/get-secret", params={"website_name": WEBSITE_NAME})
    if response.status_code != 200:
        return jsonify({"error": "Failed to retrieve secret."}), 400

    data = response.json()
    secret = data.get("secret")
    if not secret:
        return jsonify({"error": "Secret not found."}), 400

    # Generate a TOTP code
    totp = pyotp.TOTP(secret, digits=10)
    current_time = int(time.time())
    time_remaining = 30 - (current_time % 30)
    current_code = totp.now()
    
    # Return the generated code and the remaining time
    return jsonify({"code": current_code, "time_remaining": time_remaining})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
