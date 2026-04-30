import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email import encoders
from django.conf import settings
from .models import CustomUser
from file.models import Document

import requests


def send_email(api_key, sender_email, recipient_email, subject, message):
    url = "https://api.brevo.com/v1/email/send"

    payload = {
        "to": recipient_email,
        "from": sender_email,
        "subject": subject,
        "message": message
    }

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email. Status code: {response.status_code}")
        print(response.json())


def share_brevo(pk, sender_id, receiver_email):
    sender = CustomUser.objects.get(pk=sender_id)
    subject = 'A file has been shared with you by {}'.format(sender.company_name)
    api_key = settings.BREVO_API_KEY
    try:
        with open('templating/email.html', 'r') as file:
            html_content = file.read()
    except Exception as e:
        print('File not read because of {}'.format(e))
    doc = Document.objects.get(pk=pk)
    url = "https://api.brevo.com/v1/email/send"

    payload = {
        "to": receiver_email,
        "from": settings.EMAIL_HOST_USER,
        "subject": subject,
        "message": html_content,
    }

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email. Status code: {response.status_code}")
        print(response.json())
