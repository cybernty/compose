# Calibre Web

- [kovidgoyal/calibre: The official source code repository for the calibre ebook manager](https://github.com/kovidgoyal/calibre)
- [janeczku/calibre-web: :books: Web app for browsing, reading and downloading eBooks stored in a Calibre database](https://github.com/janeczku/calibre-web)
    - [linuxserver/calibre-web - Docker Image | Docker Hub](https://hub.docker.com/r/linuxserver/calibre-web)

## Quick Start

- [calibre-web/README.md at master · janeczku/calibre-web · GitHub](https://github.com/janeczku/calibre-web/blob/master/README.md#quick-start)

```sh
docker compose up -d
curl -O -L https://github.com/janeczku/calibre-web/raw/master/library/metadata.db
sudo chmod 777 -R calibre
mv metadata.db calibre/library
```

## Config

1. choose database file
2. change password
3. enable upload
