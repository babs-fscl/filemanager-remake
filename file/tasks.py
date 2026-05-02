from django.template.loader import render_to_string
from authentication.models import CustomUser
from file.models import Document
from celery import shared_task
import requests
import json
from django.conf import settings
import tempfile
import os
from .utils import load_docx_file, load_pdf_file, load_csv_file, load_xlsx_file


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


@shared_task
def process_uploaded_file_task(doc_id):
    try:
        doc = Document.objects.get(pk=doc_id)
        if not doc.file:
            return
            
        file_type = doc.type
        content_loader = {
            'docx': load_docx_file,
            'pdf': load_pdf_file,
            'csv': load_csv_file,
            'xlsx': load_xlsx_file
        }
        
        if file_type not in content_loader:
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
            for chunk in doc.file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            content = content_loader[file_type](temp_file_path)
            doc.content = content
            doc.save()
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except Exception as e:
        print(f"Error in process_uploaded_file_task: {e}")
