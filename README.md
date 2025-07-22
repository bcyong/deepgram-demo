# Deepgram Demo Project: Transcription & Audio Intelligence Platform

This project demonstrates the use of Deepgram’s speech recognition and Audio Intelligence capabilities in a stateless, containerized API service.

The system is designed to simulate a realistic customer implementation scenario that supports asynchronous batch transcription with webhook-based results delivery, rich audio intelligence analysis, custom keyword handling, and validation tooling - all optimized for minimal workflow disruption and extensibility.

---

## Features

### Core Capabilities
- **Batch transcription of audio URLs** using Deepgram's asynchronous API
- **Webhook support** for processing transcription results with:
  - Automatic summarization
  - Sentiment analysis
  - Topic and intent detection
  - Speaker diarization and segment-level timestamps
- **Keyword boosting and keyterm support** with runtime configurability via API
- **WER audit endpoints** for validating Deepgram output against reference transcripts
- **Metadata and user callback support**: maintain stateless job tracking across webhook flow

### ⚙️ Architecture & Ops
- **FastAPI backend**, with typed request/response models and built-in interactive API docs
- **Containerized (Docker)** and designed for **stateless, horizontally scalable deployment**
- Uses **Redis** for dynamic keyword/keyterm storage and potential queueing
- Stores transcription results in **Google Cloud Storage (GCS)** by default
- Modular design to support future integration with streaming audio (WebSocket) or alternative storage backends

---

## Project Structure

```text
deepgram-demo/
│
├── app/                        # Main application package
│   ├── main.py                 # FastAPI app factory
│   ├── routers/               # Modular API route definitions
│   │   ├── audit.py           # WER audit endpoints
│   │   ├── health.py          # Liveness/readiness checks
│   │   ├── keyword.py         # API for managing boosted keywords
│   │   ├── keyterm.py         # API for managing keyterms (Nova-compatible)
│   │   ├── transcribe.py      # Batch transcription submission
│   │   └── webhook.py         # Deepgram callback handler
│   ├── utils/                 # Core logic utilities
│   │   ├── deepgram_client.py         # Wrapper around Deepgram SDK
│   │   ├── deepgram_parser.py         # Summary, sentiment, intent, diarization logic
│   │   ├── storage_client.py          # GCS integration
│   │   ├── keyword_manager.py         # Keyword Redis storage
│   │   ├── keyterm_manager.py         # Keyterm Redis storage
│   │   └── wer.py                     # WER calculation via `jiwer`
│   └── models/               # Pydantic request/response models
│
├── pyproject.toml            # Dependency and tool declarations
├── Dockerfile                # Container build instructions
├── .env.template             # Example environment config
├── README.md                 # You are here
└── requirements.txt          # (optional) legacy pip support

---

## Key Endpoints

| Method | Route                                                   | Description                                                      |
|--------|----------------------------------------------------------|------------------------------------------------------------------|
| POST   | `/api/v1/transcribe/batch-url`                          | Submit one or more audio URLs for Deepgram transcription         |
| POST   | `/api/v1/webhook/deepgram/batch_url_completed`          | Deepgram callback receiver for transcription results             |
| POST   | `/api/v1/audit/text`                                    | Compare reference and hypothesis transcripts for WER             |
| POST   | `/api/v1/audit/audio-url`                               | Compare a Deepgram transcript (from URL) against reference       |
| POST   | `/api/v1/audit/audio-file`                              | Same as above but with uploaded file                             |
| POST   | `/api/v1/keyword/add`                                   | Add keywords and boost values to use in requests                 |
| DELETE | `/api/v1/keyword/delete`                                | Remove stored boosted keywords                                   |
| GET    | `/api/v1/keyword/list`                                  | View current stored keywords                                     |
| POST   | `/api/v1/keyterm/add`                                   | Add keyterms (Nova-compatible)                                   |
| DELETE | `/api/v1/keyterm/delete`                                | Remove stored keyterms                                           |
| GET    | `/api/v1/keyterm/list`                                  | View current stored keyterms                                     |
| GET    | `/api/v1/health`                                        | Health and readiness checks                                      |

Interactive OpenAPI docs available at:  
**`http://localhost:8000/docs`**

---

## Setup and Usage

### 1. Clone and Configure

```bash
git clone https://github.com/bcyong/deepgram-demo.git
cd deepgram-demo
cp .env.template .env
# Edit .env with your DEEPGRAM_API_KEY, Redis, and GCS settings
```

### 2. Run with Docker

```bash
docker build -t deepgram-demo .
docker run --env-file .env -p 8000:8000 deepgram-demo
```

### Requirements

- A running Redis instance (local or Docker-based)
- A valid Google Cloud Storage bucket with proper permissions
- Set the ```GOOGLE_APPLICATION_CREDENTIALS``` environment variable to your GCP service account JSON

---

## Notes for Evaluation

- Core batch transcription and Audio Intelligence features are implemented
- Modular, stateless API design with strong use of metadata
- Realistic webhook and storage integration (Google Cloud Storage)
- Designed for extensibility (e.g., future support for streaming, storage routing)
- Real-time streaming (WebSocket) not yet implemented
- User-defined callback URL support is scaffolded but not yet executed
- Keyword spotting logic is present but not yet reflected in final response formatting

## Future Enhancements

- Add WebSocket endpoint for real-time streaming transcription
- Implement file-based transcription submission (upload + synchronous response)
- Add result polling endpoints by batch ID or job ID
- Create a simple UI for managing transcription jobs and tuning keyword/keyterm lists
- Introduce queue-based concurrency controller for managing Deepgram rate limits
- Extend support for alternate cloud storage backends (e.g., AWS S3)
