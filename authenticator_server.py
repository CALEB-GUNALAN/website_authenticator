from flask import Flask, request, jsonify, render_template
import pyotp
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)

# In-memory storage for registered websites (use a database for production)
registered_websites = {}

@app.route('/')
def home():
    return """
    <!-- Favicon -->
<link rel="icon" type="image/png" href="/static/favicon.png">       
<title>Authenticator Server</title>
<style>
    /* Gradient Background from the first snippet */
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .gradient-bg {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    body, html {
        height: 100%;
        margin: 0;
        font-family: Arial, sans-serif;
    }

    .container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100%;
        text-align: center;
    }

    .content {
        background-color: #f0f0f0;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    h1 {
        color: #333;
        margin-bottom: 1.5rem;
    }

    .button-container {
        display: flex;
        gap: 1rem;
        margin-top: 1.5rem;
    }

    .button {
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        text-decoration: none;
        color: white;
        background-color: #4CAF50;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    .button:hover {
        background-color: #45a049;
    }

    .button.verify {
        background-color: #008CBA;
    }

    .button.verify:hover {
        background-color: #007B9E;
    }
</style>
</head>
<body class="gradient-bg">
    <div class="container">
        <div class="content">
            <h1>Authenticator Server</h1>
            <div class="button-container">
                <a href="/register" class="button">Register</a>
                <a href="/verify" class="button verify">Verify</a>
            </div>
        </div>
    </div>
</body>
</html>

    """

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':
        data = request.get_json()
        website_name = data.get('website_name')
        if not website_name:
            return jsonify({"error": "Website name is required."}), 400

        if website_name in registered_websites:
            return jsonify({"error": "Website already registered."}), 400

        # Generate a unique secret key for the website
        secret = pyotp.random_base32()
        registered_websites[website_name] = secret

        # Generate a QR code
        otp_provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=website_name, issuer_name="Website Authenticator")
        qr = qrcode.make(otp_provisioning_uri)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return jsonify({"secret": secret, "qr_code": img_str}), 200

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'GET':
        return render_template('verify.html')
    
    if request.method == 'POST':
        data = request.get_json()
        website_name = data.get('website_name')
        user_code = data.get('code')

        if not website_name or not user_code:
            return jsonify({"error": "Website name and code are required."}), 400

        secret = registered_websites.get(website_name)
        if not secret:
            return jsonify({"error": "Website not registered."}), 400

        totp = pyotp.TOTP(secret, digits=10)
        if totp.verify(user_code):
            return jsonify({"status": "Original", "website_name": website_name}), 200
        else:
            return jsonify({"status": "Fake or Invalid Code"}), 400
        
@app.route('/get-secret', methods=['GET'])
def get_secret():
    website_name = request.args.get('website_name')
    if not website_name:
        return jsonify({"error": "Website name is required."}), 400

    secret = registered_websites.get(website_name)
    if not secret:
        return jsonify({"error": "Website not registered."}), 400

    return jsonify({"secret": secret}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
