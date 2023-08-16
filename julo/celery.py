import os

from dotenv import load_dotenv
from celery import Celery

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'julo.settings')

app = Celery('julo')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Configure the broker and result backend using RabbitMQ
app.conf.broker_url = os.getenv("CELERY_BROKER_URL")
app.conf.result_backend = 'rpc://'

# Optional: Define a default queue for tasks
app.conf.task_default_queue = 'default'

if __name__ == '__main__':
    app.start()
