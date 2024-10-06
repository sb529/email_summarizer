from flask import Flask, request, jsonify
from main import summarize_email  # Correct import

app = Flask(__name__)

@app.route('/summarize_email', methods=['POST'])
def summarize_email_route():
    try:
        email_body = request.json.get('email_body')
        sender_email = request.json.get('sender_email')

        # Call the summarize_email function here
        summary = summarize_email(email_body)

        # Send back a JSON response with the summary
        return jsonify({"summary": summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
