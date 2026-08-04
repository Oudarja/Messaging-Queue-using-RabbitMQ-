# RabbitMQ + Celery + FastAPI + Telegram Bot Integration

## Overview

This project demonstrates how to process Telegram messages asynchronously using:

- FastAPI
- Celery
- RabbitMQ
- Telegram Bot API
- Docker
- ngrok

Instead of processing Telegram messages inside the webhook request, the webhook immediately sends the message to RabbitMQ, where Celery workers process it in the background. This makes the application scalable and responsive.

---

# Architecture

```
                Telegram User
                      │
                      │
                      ▼
              Telegram Servers
                      │
             HTTPS Webhook Request
                      │
                      ▼
                ngrok Tunnel
                      │
                      ▼
             FastAPI Webhook (/telegram/webhook)
                      │
        process_telegram_message.delay(...)
                      │
                      ▼
                 RabbitMQ Queue
                      │
                      ▼
                 Celery Worker
                      │
          Process Message (Heavy Task)
                      │
                      ▼
           Telegram Bot sendMessage API
                      │
                      ▼
                Telegram User
```

---

# Technologies Used

- Python
- FastAPI
- Celery
- RabbitMQ
- Docker
- Telegram Bot API
- ngrok
- Requests
- python-dotenv

---

# Project Flow

## Step 1

User sends a message to the Telegram Bot.

Example:

```
Hi
```

---

## Step 2

Telegram sends the message to the configured webhook.

```
POST /app/v0/telegram/webhook
```

---

## Step 3

FastAPI receives the request.

It extracts

- chat_id
- text

Example:

```python
message = {
    "chat_id": chat_id,
    "text": message_text
}
```

---

## Step 4

Instead of processing immediately,

FastAPI sends the task to RabbitMQ.

```python
process_telegram_message.delay(message)
```

FastAPI immediately returns

```json
{
    "status": "Message queued"
}
```

The webhook finishes within milliseconds.

---

## Step 5

RabbitMQ stores the task inside its queue.

```
Telegram
      │
      ▼
 RabbitMQ Queue
```

---

## Step 6

Celery Worker continuously listens to RabbitMQ.

```
celery -A tasks worker --pool=solo --loglevel=info
```

Whenever a new task arrives,

Celery automatically picks it.

---

## Step 7

Celery processes the message.

Example:

```python
time.sleep(5)
```

Simulates a long-running task.

---

## Step 8

Worker sends the response back to Telegram.

```python
requests.post(
    f"{TELEGRAM_API}/sendMessage",
    json=payload
)
```

Telegram user receives

```
Received your message: Hi
```

---

---

# RabbitMQ Installation on Windows

## 1. Instead of installing RabbitMQ natively, RabbitMQ was deployed using Docker.

```
rabbitmq:management
```

Docker exposes

```
5672
```

for AMQP communication

and

```
15672
```

for the RabbitMQ Management UI.

Advantages:

- Easier installation
- No Erlang installation
- Cross-platform
- Consistent environment

---

## 2. Verifying RabbitMQ Status

Needed to verify RabbitMQ was actually running.

Used

```
docker ps
```

to verify container status.

Also checked

```
docker inspect rabbitmq
```

to verify:

- exposed ports
- container IP
- running state

RabbitMQ Management Dashboard:

```
http://localhost:15672
```

Default credentials

```
guest
guest
```
<img width="1000" height="500" alt="image" src="https://github.com/user-attachments/assets/55966086-5164-481a-9d79-83f99c5d6d20" />

---
# Technical Challenges Faced

## 1. Celery on Windows

### Challenge

Celery's default multiprocessing pool is not fully compatible with Windows.

Errors included worker crashes and process spawning issues.

Examples included:

- SpawnPoolWorker errors
- WinError 5
- WinError 6
- billiard pool exceptions

---

### Solution

Run Celery using the Solo Pool.

```
celery -A tasks worker --pool=solo --loglevel=info
```

Why?

The Solo Pool executes tasks in a single process, avoiding Windows multiprocessing limitations.

---

## 2. RabbitMQ Connection

### Challenge

Celery needed to connect correctly to RabbitMQ.

---

### Solution

Broker configuration:

```python
Celery(
    "myapp",
    broker="amqp://guest:guest@localhost:5672//"
)
```

Successfully connected to the RabbitMQ Docker container.

---

## 3. Telegram Webhook Requires HTTPS + ngrok Agent Version
 
### Challenge
Telegram does **not** allow webhook URLs that use:
```
http://localhost:8000
```
or
```
127.0.0.1
```
Telegram servers cannot access local machines directly. On top of that, older ngrok versions couldn't even establish a tunnel, throwing errors like:
```
ERR_NGROK_121
authentication failed
Your ngrok-agent version is too old
```
 
### Solution
Use **ngrok** to create a secure public HTTPS URL that forwards requests to the local FastAPI server:
```
https://xxxx.ngrok-free.app
        │
        ▼
localhost:8000
```
 
**1. Install and verify the latest ngrok version:**
```
ngrok version
```
Example:
```
3.39.x
```
 
**2. Create a free ngrok account and configure the authentication token.**
 
After creating a free ngrok account, the authentication token provided by ngrok was configured using:
```
ngrok config add-authtoken <YOUR_AUTH_TOKEN>
```
 
Example:
```
ngrok config add-authtoken 2abcXYZxxxxxxxxxxxx
```
 
This command stores the authentication credentials locally and allows the ngrok agent to create authenticated tunnels.
 
**3. Start the HTTPS tunnel.**
 
After configuring the authentication token, an HTTPS tunnel was created for the FastAPI application running on port `8000`.
 
Command:
```
ngrok http 8000
```
 
ngrok generated a public HTTPS forwarding URL:
```
Forwarding
 
https://abc123.ngrok-free.app  →  http://localhost:8000
```
 
The generated HTTPS URL allows Telegram servers to communicate with the locally running FastAPI application.

---

## 4. Telegram Webhook Configuration

Webhook was configured using:

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://abc123.ngrok-free.app/app/v0/telegram/webhook
```
Where:

- `<TOKEN>` represents the unique authentication token generated by **BotFather** for the Telegram bot.
- `https://abc123.ngrok-free.app` is the publicly accessible HTTPS URL generated by ngrok.
- `/app/v0/telegram/webhook` is the FastAPI endpoint responsible for receiving Telegram updates.

When this URL is opened in a browser, Telegram registers the provided webhook endpoint and returns a confirmation response:

```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```
Telegram then automatically forwards every incoming message to FastAPI.


---

## 5. Environment Variables

Sensitive information should never be hardcoded.

Example `.env`

```
TELEGRAM_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxx
```

Python:

```python
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
```

---

## 6. Asynchronous Processing

Without Celery

```
Telegram
      │
      ▼
 FastAPI
      │
 Heavy Processing
      │
 Telegram waits...
```

With Celery

```
Telegram
      │
      ▼
FastAPI
      │
      ▼
RabbitMQ
      │
      ▼
Celery Worker
      │
Heavy Processing
```

Benefits

- Fast webhook response
- Non-blocking API
- Background task execution
- Scalable architecture

---

# Running the Project

## 1. Start RabbitMQ

```bash
docker start rabbitmq
```

---

## 2. Start FastAPI

```bash
uvicorn main:app --reload
```

---

## 3. Start Celery Worker

```bash
celery -A tasks worker --pool=solo --loglevel=info
```

---

## 4. Start ngrok

```bash
ngrok http 8000
```

---

## 5. Configure Telegram Webhook

Use the generated ngrok HTTPS URL:

```
https://<ngrok-url>/app/v0/telegram/webhook
```

---

## 6. Test

Send

```
Hi
```

to your Telegram Bot.

Flow:

```
Telegram
    │
    ▼
FastAPI
    │
.delay()
    │
RabbitMQ
    │
Celery Worker
    │
sendMessage()
    │
Telegram User
```

Expected reply:

```
Received your message: Hi
```

---

# Benefits of This Architecture

- Non-blocking API
- Background task processing
- Scalable workers
- Reliable message queue
- Decoupled architecture
- Easy monitoring with RabbitMQ Management UI
- Secure webhook integration via ngrok

---

# Future Improvements

- Retry failed tasks
- Dead Letter Queues (DLQ)
- Task result backend (Redis)
- Multiple Celery workers
- Task prioritization
- Scheduled tasks with Celery Beat
- Docker Compose for full orchestration
- Deployment to cloud platforms (AWS, Azure, GCP)
