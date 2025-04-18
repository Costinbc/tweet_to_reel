FROM python:3.12-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx ffmpeg && \
    apt-get clean

WORKDIR /app

# Copy your files
COPY . .

# Install Python deps
RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "src/app.py"]
