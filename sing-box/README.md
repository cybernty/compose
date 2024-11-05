# sing-box

- [SagerNet/sing-box: The universal proxy platform](https://github.com/SagerNet/sing-box)

## Run

```sh
# server

bash certificate.sh
vi config.server.json
docker compose -f compose.server.yaml up -d
docker compose -f compose.server.yaml logs
# docker compose -f compose.server.yaml down
```

```sh
# client

vi config.client.json
docker compose -f compose.client.yaml up -d
docker compose -f compose.client.yaml logs
# docker compose -f compose.client.yaml down
# webui: 127.0.0.1:9090
```
