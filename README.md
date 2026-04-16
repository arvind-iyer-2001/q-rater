# Q-Rater

A full-stack content intelligence pipeline that ingests Instagram Reels and YouTube videos, processes them through a multi-modal LLM pipeline, stores vector embeddings in MongoDB Atlas, and serves personalized content recommendations via an agentic RAG pipeline.

## Architecture

```
URL Input
  └─► IngestDispatcher ──► YouTubeIngester / InstagramIngester
           │                        │ (yt-dlp / instaloader)
           │                        ▼
           │              RawMedia (video, audio, captions, comments)
           │                        │
           └──► ProcessingPipeline ─┤
                    │               ├─ WhisperTranscriber (audio → transcript)
                    │               ├─ extract_keyframes (video → JPEG frames)
                    │               ├─ OllamaMultiModalAnalyzer (gemma4)
                    │               └─ VoyageEmbedder (1024-dim embeddings)
                    │
                    ▼
              ContentDocument ──► MongoDB Atlas (Vector Search)
                                          │
                                          ▼
                               RAGAgent (Ollama + tool use)
                                  └─ VectorRetriever ($vectorSearch)
                                  └─ PersonalizedRecommender
```

## Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + uvicorn |
| Task Queue | ARQ + Redis |
| Ingestion | yt-dlp, instaloader |
| Transcription | OpenAI Whisper |
| LLM Analysis | Ollama (gemma4) |
| Embeddings | Voyage AI `voyage-large-2-instruct` (1024-dim) |
| Vector DB | MongoDB Atlas Vector Search |
| Frontend | Next.js 14 + Tailwind CSS |
| Container | Docker + docker-compose |

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/arvind-iyer-2001/q-rater
cd q-rater
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

### 2. Required API Keys

- **`VOYAGE_API_KEY`** — [dash.voyageai.com](https://dash.voyageai.com)
- **`MONGODB_URI`** — MongoDB Atlas connection string ([cloud.mongodb.com](https://cloud.mongodb.com))

### 3. Create MongoDB Atlas Vector Search Index

```bash
cd backend
pip install -r requirements.txt
python scripts/create_vector_index.py
```

### 4. Run with Docker Compose

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### 5. Run without Docker (development)

```bash
# Terminal 1: Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Backend API
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3: ARQ Worker
cd backend
arq app.tasks.worker.WorkerSettings

# Terminal 4: Frontend
cd frontend
npm install
npm run dev
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/ingest` | Submit YouTube or Instagram URL |
| `GET` | `/api/ingest/{job_id}/status` | Poll ingestion job status |
| `GET` | `/api/content` | List ingested content |
| `GET` | `/api/content/{id}` | Get content detail with transcript |
| `POST` | `/api/search` | Agentic RAG search query |
| `GET` | `/api/recommendations?user_id=` | Personalized recommendations |
| `POST` | `/api/users/{user_id}/interests` | Update user interests |

### Ingest a video

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

Response:
```json
{"job_id": "...", "content_id": "...", "status": "pending"}
```

### Poll status

```bash
curl http://localhost:8000/api/ingest/{job_id}/status
```

### Semantic search

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Python tutorial for beginners", "user_id": "guest"}'
```

## Project Structure

```
q-rater/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── ingestion/    # YouTube + Instagram scrapers
│   │   ├── processing/   # Whisper, Ollama, Voyage pipelines
│   │   ├── rag/          # Agentic RAG + recommender
│   │   ├── storage/      # MongoDB models + queries
│   │   ├── tasks/        # ARQ background worker
│   │   └── utils/        # File utils, URL parser
│   ├── scripts/          # Atlas index setup
│   └── tests/
└── frontend/
    ├── pages/            # Next.js pages
    ├── components/       # React components
    └── lib/              # Typed API client
```

## MongoDB Atlas Vector Index

The index must be created manually via the Atlas UI or the setup script. Configuration:

```json
{
  "fields": [
    {"type": "vector", "path": "embeddings.combined", "numDimensions": 1024, "similarity": "cosine"},
    {"type": "filter", "path": "source"},
    {"type": "filter", "path": "summary.content_type"},
    {"type": "filter", "path": "summary.language"}
  ]
}
```

## Notes

- Instagram ingestion requires a public account or valid session cookies (`INSTAGRAM_SESSION_ID`)
- Whisper `base` model is used by default; use `medium` or `large` for better accuracy at the cost of speed
- The ARQ worker is optional; without Redis, jobs run in-process (slower, no parallelism)
- Video files are downloaded to `MEDIA_TEMP_DIR` and cleaned up after processing
