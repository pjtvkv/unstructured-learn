# Unstructured Learn

FastAPI service that wraps [unstructured.io](https://unstructured.io) to extract
structured content from common business documents (PDF, DOCX, PPTX, etc.).

The service exposes a simple upload endpoint, making it easy to experiment with
document parsing locally or embed into larger applications.

## Project layout

```
.
├── app
│   ├── __init__.py           # Package marker
│   ├── extraction.py         # Utilities that call unstructured.partition
│   └── main.py               # FastAPI application and routes
├── docker-compose.yml        # Convenience runner with hot reload
├── Dockerfile                # Production-ready image definition
└── requirements.txt          # Python dependencies
```

## Prerequisites

- Python 3.11+ (if running locally without Docker)
- Docker & Docker Compose (optional but recommended)
- System dependencies needed by `unstructured` are installed automatically in
  the Docker image. When running natively, make sure tools like `libmagic`,
  `poppler-utils`, `tesseract-ocr`, and `libreoffice` are available.

## Local setup (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit <http://127.0.0.1:8000/docs> for the interactive Swagger UI.

## Using Docker Compose

```bash
docker compose up --build
```

Compose mounts the repository into the container so code changes trigger live
reloads. Stop with `Ctrl+C`.

## API usage

- `GET /health` – Liveness probe
- `POST /v1/extract` – Upload one or more files. Returns the list of
  unstructured elements detected in each document.

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/v1/extract" \
  -F "files=@/path/to/document.pdf" \
  -F "files=@/path/to/slide-deck.pptx"
```

Key response fields:

- `filename`: Original filename provided by the client.
- `elements`: Array of dictionaries returned from `unstructured`, each
  containing fields such as `type`, `text`, and `metadata`.

## Supported formats

`app/extraction.py` contains `SUPPORTED_EXTENSIONS`, which governs basic file
validation. Update the list or remove the guard if you prefer to defer
validation to the `unstructured` library.

## Next steps

- Add authentication/authorization if exposing the service outside a trusted
  network.
- Persist extraction results or push them into downstream pipelines.
- Extend tests and logging as you adapt the service for production workloads.
