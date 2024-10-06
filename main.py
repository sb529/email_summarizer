import os
import base64
import openai  # Correct OpenAI import
from openai import OpenAI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from main import summarize_email

# Load environment variables from the .env file
load_dotenv(dotenv_path='/Users/sbhargav/.cursor-tutor/email_summarizer/.env')

# Access the OpenAI API key from the .env file
openai.api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai.api_key)  # Correct client instantiation

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.modify']
creds = None

# Load credentials from token.json
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('/Users/sbhargav/.cursor-tutor/email_summarizer/token.json', SCOPES)

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


def format_summary_as_paragraphs_and_bullets(summary_text):
    # Split the summary text into sentences
    sentences = summary_text.split('. ')

    formatted_summary = ''
    # Rejoin sentences into formatted paragraphs and add bullet points
    for i in range(0, len(sentences), 3):  # Adjust the number of sentences per paragraph
        paragraph = '. '.join(sentences[i:i + 3]) + '.'
        if i == 0:  # For the first paragraph, don't use bullet points
            formatted_summary += paragraph + '\n\n'
        else:
            # Use bullet points for subsequent paragraphs
            formatted_summary += '\u2022 ' + paragraph.strip() + '\n'
    
    return formatted_summary.strip()

def summarize_email(email_body):
    # Define the maximum length for each chunk
    max_length = 4000  # Adjust this value based on the token limit

    # Split the email body into chunks
    chunks = [email_body[i:i + max_length] for i in range(0, len(email_body), max_length)]

    summaries = []

    # Summarize each chunk separately
    for chunk in chunks:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Or "gpt-4" if available
        messages=[
        {"role": "system", "content": "You are an email summarizer."},
         {"role": "user", "content": f"Summarize this email thread:\n{chunk}"}
    ],
    max_tokens=150
)

# Correct way to access the response content
    summaries.append(response.choices[0].message.content.strip())


    # Combine all chunk summaries into a final summary
    final_summary = " ".join(summaries)
    formatted_summary = format_summary_as_paragraphs_and_bullets(final_summary)  # For paragraphs
    return formatted_summary


def send_summary_email(service, to_email, summary):
    msg = MIMEText(summary)
    msg['to'] = to_email
    msg['from'] = 'summarygen8@gmail.com'
    msg['subject'] = 'Summary of Your Email Thread'

    try:
        send_message = service.users().messages().send(userId="me", body={'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}).execute()
        print(f'Message sent: {send_message["id"]}')
    except HttpError as error:
        print(f'An error occurred: {error}')

def delete_email(service, message_id):
    try:
        # Delete the email from the inbox using the message_id
        service.users().messages().delete(userId='me', id=message_id).execute()
        print(f"Deleted email with ID: {message_id}")
    except HttpError as error:
        print(f'An error occurred while deleting the email: {error}')

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
