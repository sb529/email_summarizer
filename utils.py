import os
import base64
import openai
from dotenv import load_dotenv
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError


# Load environment variables from the .env file
load_dotenv(dotenv_path='.env')

# Access the OpenAI API key from the .env file
openai.api_key = os.getenv('OPENAI_API_KEY')
client = openai

def summarize_email(email_body):
    # Define the maximum length for each chunk
    max_length = 4000  # Adjust this value based on the token limit

    # Split the email body into chunks
    chunks = [email_body[i:i + max_length] for i in range(0, len(email_body), max_length)]
    summaries = []

    # Summarize each chunk separately
    for chunk in chunks:
        response = client.chat.completions.create(model="gpt-3.5-turbo",  # Or "gpt-4" if available
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

def send_summary_email(service, to_email, summary):
    msg = MIMEText(summary)
    msg['to'] = to_email
    msg['from'] = 'summarygen8@gmail.com'
    msg['subject'] = 'Summary of Your Email Thread'

    try:
        send_message = service.users().messages().send(
            userId="me", 
            body={'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
        ).execute()
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
