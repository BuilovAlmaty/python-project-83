install:
	uv sync
dev:
	uv run flask --debug --app page_analyzer:app run
PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 127.0.0.1:$(PORT) page_analyzer:app
lint:
	uv run ruff check .
build:
	build.sh
render-start:
	gunicorn -w 5 -b 127.0.0.1:$(PORT) page_analyzer:app
