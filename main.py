import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from utils import summarize_email, send_summary_email, delete_email
import base64
from googleapiclient.errors import HttpError


# Load environment variables from the .env file
load_dotenv(dotenv_path='.env')

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.modify']
creds = None

# Load credentials from token.json
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# Create Gmail API service
service = build('gmail', 'v1', credentials=creds)

def get_last_email(service):
    try:
        # Get the latest email from the inbox
        result = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=1).execute()

        if 'messages' not in result:
            print("No messages found in the inbox.")
            return None, None, None

        # Get the ID of the most recent message
        message_id = result['messages'][0]['id']
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()

        # Extract the email body
        parts = message['payload']['parts']
        email_body = ''
        for part in parts:
            if part['mimeType'] == 'text/plain':
                email_body = part['body']['data']
                email_body = base64.urlsafe_b64decode(email_body).decode('utf-8')
                break

        # Get the sender's email address
        headers = message['payload']['headers']
        sender_email = next(header['value'] for header in headers if header['name'] == 'From')

        return email_body, sender_email, message_id
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None, None, None

def main():
    # Get the latest email
    email_body, sender_email, message_id = get_last_email(service)

    if not email_body:
        print("No email found to summarize.")
        return

    # Summarize the email
    summary = summarize_email(email_body)

    # Send the summary back to the sender
    send_summary_email(service, sender_email, summary)

    # Delete the original email
    delete_email(service, message_id)

if __name__ == "__main__":
    main()
