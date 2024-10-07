from flask import Flask, request, jsonify
from utils import summarize_email  # Import the summarize_email function from utils

app = Flask(__name__)

@app.route('/summarize_email', methods=['POST'])
def summarize_email_route():
    try:
        # Get the email body and sender's email from the JSON request
        email_body = request.json.get('email_body')
        
        # Check if email_body is provided
        if not email_body:
            return jsonify({"error": "email_body is required"}), 400

        # Call the summarize_email function from utils.py
        summary = summarize_email(email_body)

        # Return the summary in JSON format
        return jsonify({"summary": summary})

    except Exception as e:
        # Return an error message in JSON format
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
