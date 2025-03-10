from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from twilio.rest import Client

app = Flask(__name__)

# Load Service Account Credentials
SERVICE_ACCOUNT_FILE = "meet-automation-453304-fb8ebca0fd6a.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Create Google Calendar API client
service = build("calendar", "v3", credentials=credentials)

# Twilio Credentials
TWILIO_SID = "AC76a37f6822b41d24891a113ea2391282"
TWILIO_AUTH_TOKEN = "b758a401964c59720cf86ead9734ed08"
TWILIO_PHONE_NUMBER = "+14155238886"
RECIPIENT_PHONE_NUMBER = "+917619239143"  # Format: whatsapp:+1234567890

def extract_meeting_details(message):
    pattern = r"Schedule a meeting at (\d{1,2}:\d{2} [APM]{2}) on (\d{2}/\d{2}/\d{4}) for (\d+) hour"
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        time, date, duration = match.groups()
        return time, date, int(duration)
    return None

def schedule_meeting(time, date, duration):
    start_time = datetime.strptime(f"{date} {time}", "%d/%m/%Y %I:%M %p")
    end_time = start_time + timedelta(hours=duration)
    
    event = {
        "summary": "Scheduled Meeting",
        "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
        "conferenceData": {"createRequest": {"requestId": "random-string"}},
    }
    
    event = service.events().insert(
        calendarId="intelliqaz18@gmail.com", body=event, conferenceDataVersion=1
    ).execute()
    
    meeting_link = event["htmlLink"]
    send_whatsapp_message(meeting_link)
    return meeting_link

def send_whatsapp_message(meeting_link):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your Google Meet link: {meeting_link}",
        from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
        to=f"whatsapp:{RECIPIENT_PHONE_NUMBER}"
    )
    print("WhatsApp message sent!")

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()
    
    meeting_details = extract_meeting_details(incoming_msg)
    if meeting_details:
        time, date, duration = meeting_details
        meeting_link = schedule_meeting(time, date, duration)
        msg.body(f"Meeting scheduled! Link: {meeting_link}")
    else:
        msg.body("Invalid format. Please use: 'Schedule a meeting at <time> on <date dd/mm/yyyy> for <duration> hour'")
    
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
