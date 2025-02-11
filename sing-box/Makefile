.PHONY: default
default: generate

.PHONY: generate
generate:
	python generate.py
	bash certificate.sh

.PHONY: up
up:
	docker compose -f compose.yaml up -d

.PHONY: log
log:
	docker compose -f compose.yaml logs

.PHONY: down
down:
	docker compose -f compose.yaml down

.PHONY: webui
webui:
	# google-chrome-stable http://127.0.0.1:9090
	xdg-open http://127.0.0.1:9090
