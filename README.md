# Deepgram Demo Project: Transcription & Audio Intelligence Platform

This project demonstrates the use of Deepgram’s speech recognition and Audio Intelligence capabilities in a stateless, containerized API service.

The system is designed to simulate a realistic customer implementation scenario that supports asynchronous batch transcription with webhook-based results delivery, rich audio intelligence analysis, custom keyword handling, and validation tooling - all optimized for minimal workflow disruption and extensibility.

---

## Features

### Core Capabilities
- **Batch transcription of audio URLs** using Deepgram's asynchronous API
- **Webhook support** for processing transcription results with:
  - Automatic summarization
  - Sentiment analysis with confidence scores
  - Topic and intent detection
  - Speaker diarization with timestamps
- **Keyword boosting and keyterm support** with runtime configurability via API
- **WER audit endpoints** for validating Deepgram output against reference transcripts
- **User callback support** for real-time notification of transcription completion
- **Web interface** for easy transcription submission and WER auditing

### Architecture & Ops
- **FastAPI backend**, with typed request/response models and built-in interactive API docs
- **Containerized (Docker)** and designed for **stateless, horizontally scalable deployment**
- Uses **Redis** for dynamic keyword/keyterm storage and potential queueing
- Stores transcription results in **Google Cloud Storage (GCS)** by default
- **Web interface** with HTML pages for transcription and audit functionality
- Modular design to support future integration with streaming audio (WebSocket) or alternative storage backends

---

## Project Structure

```text
deepgram-demo/
│
├── app/                       # Main application package
│   ├── __init__.py            # Package initialization
│   ├── main.py                # FastAPI app factory
│   ├── dependencies.py        # Dependency injection setup
│   ├── routers/               # Modular API route definitions
│   │   ├── __init__.py        # Router package initialization
│   │   ├── audit.py           # WER audit endpoints
│   │   ├── health.py          # Liveness/readiness checks
│   │   ├── keyword.py         # API for managing boosted keywords
│   │   ├── keyterm.py         # API for managing keyterms (Nova 3-compatible)
│   │   ├── transcribe.py      # Batch transcription submission
│   │   └── webhook.py         # Deepgram callback handler
│   ├── templates/             # HTML templates for web interface
│   │   ├── index.html         # Main transcription interface
│   │   └── audit.html         # WER audit interface
│   ├── utils/                 # Core logic utilities
│   │   ├── __init__.py        # Utils package initialization
│   │   ├── deepgram_client.py # Wrapper around Deepgram SDK
│   │   ├── deepgram_parser.py # Summary, sentiment, intent, diarization logic
│   │   ├── google_cloud_storage_client.py # GCS integration
│   │   ├── keyterm_manager.py # Keyterm Redis storage
│   │   ├── storage_client.py  # Redis client wrapper
│   │   └── wer_calculator.py  # WER calculation via `jiwer`
│   └── internal/              # Internal application modules
│       └── __init__.py        # Internal package initialization
│
├── pyproject.toml            # Dependency and tool declarations
├── uv.lock                   # Lock file for dependency versions
├── Dockerfile                # Container build instructions
├── .env.template             # Example environment config
└── README.md                 # You are here
```
---

## Key Endpoints

| Method | Route                                                   | Description                                                      |
|--------|---------------------------------------------------------|------------------------------------------------------------------|
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

## Web Interface

The application provides a user-friendly web interface for transcription and auditing:

### Main Transcription Interface
- **URL**: `http://localhost:8000/`
- **Features**:
  - Submit audio URLs for transcription
  - Configure keyterms and audio intelligence options
  - Real-time response display
  - Link to audit interface

### WER Audit Interface
- **URL**: `http://localhost:8000/audit`
- **Features**:
  - Text-to-text WER comparison
  - Audio URL WER comparison (transcribes audio first)
  - Audio file upload WER comparison
  - Detailed WER metrics display

---

## User Callback System

When a `user_callback_url` is provided in transcription requests, the system will automatically send a POST request to that URL upon completion with the following JSON payload:

```json
{
  "audio_url": "https://example.com/audio.mp3",
  "batch_id": "uuid-batch-id",
  "batch_index": 0,
  "deepgram_request_id": "deepgram-request-id",
  "output_file_location": "gs://yonger-deepgram-demo/transcriptions/filename.json",
  "summary": "Audio summary text",
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "extreme_sentiment_scores": [0.1, 0.9],
  "intents": ["intent1", "intent2"],
  "topics": ["topic1", "topic2"],
  "submitted_at": "2025-07-21T10:00:00Z",
  "completed_at": "2025-07-21T10:05:00Z"
}
```

### Callback Fields:
- **audio_url**: Original audio URL submitted for transcription
- **batch_id**: Unique batch identifier for grouping related transcriptions
- **batch_index**: Position of this transcription within the batch (0-based)
- **deepgram_request_id**: Deepgram's internal request identifier
- **output_file_location**: Full GCS path to the stored transcription result
- **summary**: Generated summary of the audio content
- **sentiment**: Overall sentiment classification (positive/negative/neutral)
- **sentiment_score**: Confidence score for sentiment analysis (0.0-1.0)
- **extreme_sentiment_scores**: Array of extreme sentiment confidence scores
- **intents**: List of detected intents in the audio
- **topics**: List of detected topics in the audio
- **submitted_at**: ISO timestamp when transcription was submitted
- **completed_at**: ISO timestamp when transcription was completed

### Error Handling:
- Callback failures are logged but don't affect webhook processing
- Network timeouts and connection errors are handled gracefully
- The webhook continues processing even if the callback fails

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
- User-friendly web interface for transcription and WER auditing
- User callback system for real-time notification of transcription completion
- Designed for extensibility (e.g., future support for streaming, storage routing)
- Real-time streaming (WebSocket) not yet implemented
- Keyword spotting logic is present but not yet reflected in final response formatting

## Future Enhancements

- Add WebSocket endpoint for real-time streaming transcription
- Implement file-based transcription submission (upload + synchronous response)
- Add result polling endpoints by batch ID or job ID
- Create a simple UI for managing transcription jobs and tuning keyword/keyterm lists
- Introduce queue-based concurrency controller for managing Deepgram rate limits
- Extend support for alternate cloud storage backends (e.g., AWS S3)
