FROM python:3.12-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy your files
COPY . .

# Install Python deps
RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "src/app.py"]
