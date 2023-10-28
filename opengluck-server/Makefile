dev:
	docker-compose up dev

start:
	docker-compose up opengluck-server

build:
	#docker-compose build --no-cache opengluck-server
	docker-compose build  opengluck-server

build-dev-tools:
	#docker-compose build --no-cache dev-tools dev
	docker-compose build dev-tools dev

clean:
	@docker-compose run --rm -u root -v opengluck-server_data:/app/data -v opengluck-server_app_node_modules:/app/app/node_modules -v opengluck-server_app_next:/app/app/.next opengluck-server ./scripts/make-clean

dev-tools:
	@[ -n "$$(docker-compose ps dev-tools --filter status=running -q)" ] || docker-compose up -d dev-tools >/dev/null

test: dev-tools
	@dev-tools/bin/exec dev-tools/scripts/pytest

lint: flake8 isort black pydocstyle pyright

flake8: dev-tools
	@dev-tools/bin/exec dev-tools/scripts/flake8

isort: dev-tools
	@dev-tools/bin/exec dev-tools/scripts/isort

black: dev-tools
	@dev-tools/bin/exec dev-tools/scripts/black

pyright: dev-tools
	@dev-tools/bin/exec dev-tools/scripts/pyright

pydocstyle: dev-tools
	@dev-tools/bin/exec dev-tools/scripts/pydocstyle

redis-cli:
	@[ -n "$$(docker-compose ps dev --filter status=running -q)" ] && docker-compose exec dev /usr/local/bin/redis-cli || docker-compose exec opengluck-server /usr/local/bin/redis-cli

release:
	scripts/release


.PHONY: build start dev clean certificate profile dev-tools lint test flake8 isort pyright pydocstyle release
