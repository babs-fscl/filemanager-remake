from django.template.loader import render_to_string
from authentication.models import CustomUser
from file.models import Document
from celery import shared_task
import requests
import json
from django.conf import settings


# celery -A fileapp worker --pool=solo -l info


@shared_task
def send_simple_download_message(doc_id, context_json):
    try:
        doc = Document.objects.get(pk=doc_id)
        context_data = json.loads(context_json)
        subject = 'File, {}, downloaded'.format(doc.name)
        
        # Use render_to_string for better template management
        content = render_to_string('emails/download_email.txt', context_data)
        
        return requests.post(
            "https://api.mailgun.net/v3/mg.neo-urban.ng/messages",
            auth=("api", settings.MAILGUN_API_KEY),
            data={"from": "Testing <postmaster@mg.neo-urban.ng>",
                  "to": [doc.user.email],
                  "subject": subject,
                  "text": content})
    except Exception as e:
        print(f"Error in send_simple_download_message: {e}")
        return None


@shared_task
def send_simple_share_message(sender_id, receiver_email, context_json):
    try:
        sender = CustomUser.objects.get(pk=sender_id)
        context_data = json.loads(context_json)
        subject = 'File Shared with You by {}'.format(sender.company_name or sender.email)
        
        # Use render_to_string for better template management
        content = render_to_string('emails/share_email.txt', context_data)
        
        return requests.post(
            "https://api.mailgun.net/v3/mg.neo-urban.ng/messages",
            auth=("api", settings.MAILGUN_API_KEY),
            data={"from": "FSCL <postmaster@mg.neo-urban.ng>",
                  "to": [receiver_email],
                  "subject": subject,
                  "text": content})
    except Exception as e:
        print(f"Error in send_simple_share_message: {e}")
        return None
