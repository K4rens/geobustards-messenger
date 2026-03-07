FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/messages.db

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 9000 9001 9002/udp

CMD ["python", "main.py"]
