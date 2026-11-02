FROM python:3.9-slim

# تثبيت FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# تثبيت المكتبات من requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]