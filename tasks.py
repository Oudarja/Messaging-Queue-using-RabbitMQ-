import time
import os
from celery import Celery
import requests

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN= os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
celery_app = Celery('myapp', broker='amqp://guest:guest@localhost:5672//')

# This Celery task will process the Telegram message asynchronously
@celery_app.task
def process_telegram_message(message):
    chat_id = message["chat_id"]
    text = message["text"]
    payload = {
        "chat_id": chat_id,
        "text": f"Received your message: {text}"
    }
    # Simulate some processing time
    time.sleep(5)

    # Send a response back to the user via Telegram API
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)
    return "message processed"

