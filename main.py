from fastapi import FastAPI, Request
import uvicorn

from tasks import process_telegram_message


app = FastAPI()

# This endpoint is used to send message to the Telegram bot via webhook. It receives the message from Telegram, extracts the chat ID and text, and then calls the Celery task to process the message asynchronously. This allows the webhook to respond quickly without waiting for the processing to complete.
@app.post("/app/v0/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data and "text" in data["message"]:
        chat_id=data["message"]["chat"]["id"]
        message_text=data["message"]["text"]

        message={
            "chat_id": chat_id,
            "text": message_text
        }
        # Call the Celery task asynchronously
        # This will queue the message for processing without
        # blocking the webhook response
        process_telegram_message.delay(message)  
        return {"status": "Message received and queued for processing for processing"}  

    return {"status": "No message text found in the request"}


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000,reload=True)