# whisper

- [openai/whisper: Robust Speech Recognition via Large-Scale Weak Supervision](https://github.com/openai/whisper)

```sh
docker build -t whisper:v1.0 .

docker run -it --name whisper -v ./:/app whisper:v1.0 -h
docker run -it --name whisper -v ./:/app whisper:v1.0 --language English /app/test.mp4
# docker start whisper
# docker logs whisper -f

```sh
docker compose run whisper --language English /app/test.mp4
```
