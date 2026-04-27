import os
import sys
from pathlib import Path

# Add the project root directory to the python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fileapp.settings')

application = get_wsgi_application()

app = application
