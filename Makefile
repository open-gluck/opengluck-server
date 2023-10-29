build:
	@cd opengluck-server && make build

build-dev-tools:
	@cd opengluck-server && make build-dev-tools

lint
	@cd opengluck-server && make lint

.PHONY: build lint
