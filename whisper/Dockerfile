FROM python:3.11

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir openai-whisper

WORKDIR /app

ENTRYPOINT ["python3", "-m", "whisper"]
CMD ["--help"]
