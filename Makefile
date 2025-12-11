PORT ?= 8000
install:
	uv sync
dev:
	uv run flask --debug --app page_analyzer:app run --host=127.0.0.1 --port=$(PORT)

build:
	./build.sh
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
kill:
	@PT=$(PT); for pid in $$(lsof -ti :$${PT:-8000}); do echo "kill pin: $$pid"; kill -9 "$$pid"; done
