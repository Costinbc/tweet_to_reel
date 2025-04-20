FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx ffmpeg && \
    apt-get clean

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "src/app.py"]
