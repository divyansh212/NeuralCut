FROM python:3.12-slim

# ffmpeg is required by the compositor (always-real composition stage).
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY streamlit ./streamlit

# Default command is the API; the worker service overrides this (see compose /
# Railway start commands). $PORT is provided by the host; defaults to 8000.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
