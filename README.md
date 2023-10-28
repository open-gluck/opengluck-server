# OpenGlück

The OpenGlück project is a collection of free software that can be used to help
build a riche ecosystem of apps and tools for diabetes users.

While it does not connect to third-party services by itself, you can use
adapters that act as plugins which you can use to record new data or query the
OpenGlück database.

## opengluck-server

This is an HTTPS server that is the main entry point of OpenGlück.

OpenGlück can be configured to call webhooks when specific events are recorded
(such as a new blood glucose reading). This is a powerful feature -- you can,
for example, write an automation that will turn on your smart lights if you're
having a low at night.

## Prerequisites

- a server, that you can use to run the software (something small is more than enough, if looking
  for a cloud instance you can use a t2.small with 16 GB of storage on AWS for around a dozen bucks per month)
- some basic knowledge about how to configure an HTTPS proxy (we recommend
  using [CaddyServer](https://caddyserver.com) for a zero-touch configuration
  of LetsEncrypt)

## Install

OpenGlück is available on
[DockerHub](https://hub.docker.com/layers/opengluck/opengluck-server). Perform
the following steps to run an OpenGlück server locally:

### 1. Pull the Docker image

```bash
docker pull opengluck/opengluck-server:latest
docker volume create opengluck-data
docker volume create opengluck-node-modules
```

### 2. Create `.env`

Create an `.env` file at the location of your chosing.

```
TZ=Europe/Paris
NEXT_PUBLIC_APP_URL=https://public-url-of-your-app.example.com
```

See the Environment section for more information about the variables you can configure.

### 3. Run the opengluck server

Run your server with Docker:

```bash
docker run -d --env-file .env \
  -v opengluck-data:/app/data \
  -v opengluck-node-modules:/app/app/node_modules \
  -p 8080:8080 --restart unless-stopped \
  --add-host host.docker.internal:host-gateway \
  opengluck/opengluck-server
```

## Environment

In addition to the environment variables accepted by Next, Here is a list of
variables you can configure in your environment:

### `TZ`

The user timezone. Defaults to `UTC`. You can give a format compatible with
[pytz](https://pypi.org/project/pytz/) such as `Europe/Paris`.

### `MERGE_RECORD_LOW_THRESHOLD`

This is optional. When set, then any scan value under this threshold will
trigger the `glucose:changed` webhook.

### `MERGE_RECORD_HIGH_THRESHOLD`

This is optional. When set, then any normal scan value crossing this threshold
will trigger the `glucose:changed` webhook.

## Local Development

### Build Images

Run the following command on the top directory to build the images:

```bash
make build
```

Create your env file at `opengluck-server/.env`.

### Installation

To build the dev environment:

```bash
make build-dev-tools
```

To check style (flake8, black, isort, pydocstyle, pyright, prettier…):

```bash
make lint
```

### Run in Dev Mode

To run both the Python server (with auto-reload) and the Next.js app (in dev
mode):

```bash
make dev
```

Doing so will let you access the front-end using the development port (by default 8080):

http://localhost:8080
