# OpenGlück Server

This is an HTTPS server that is the main entry point of OpenGlück.

While it does not connect to third-party services by itself, you can use
adapters that act as plugins which you can use to record new data or query the
OpenGlück database.

OpenGlück can be configured to call webhooks when specific events are recorded
(such as a new blood glucose reading). This is a powerful feature -- you can,
for example, write an automation that will turn on your smart lights if you're
having a low at night.

## Prerequisites

- a server computer or virtual machine, that you can use to run the software (something small is more than enough, if looking
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

This will listen on HTTP traffic on port `8080`. This port needs not be open on remote interfaces, see step below.

### 4. Forward HTTPS requests to `opengluck-server`

Use the software of your chosing to forward HTTPS requests to your SSL domain name to OpenGlück.

I am told you can use Caddy like so (replace `example.com` with your domain name):

```
docker run caddy:latest caddy reverse-proxy --from example.com --to localhost:8080
```

## Usage

The OpenGlück server is a “dumb” piece of software, that does not attempt to collect glucose data by itself, or to perform actions when certain conditions occur.

You are free to enable the plug-ins you want, or write your own if you'd like to.

The basic idea is:

1. To inject data to OpenGlück, you use one of the APIs to upload records.
2. To trigger a plug-in when “something” occurs, you need to add a webhook. This is a URL that your plug-ins listen to, typically on `localhost`. When the specific action accurs, OpenGlück calls your plug-in with a JSON payload so you have more context. If required, you can always use APIs to retrieve more data from OpenGlück.

## Concepts

### Records

Records are either:

- glucose readings
- insulin (bolus)
- low (also known as “snacks”)

#### Glucose Readings

Glucose readings can be of two type:

- `historic`: these are the records that have been processed by whichever smoothing algorithm your reader is using. These values are not expected to change.
- `scan`: these are the “fresh” records, which might be adjusted in a near future to smooth readings.

#### Insulin

Insulin records are always boluses.

#### Low/Snack

A low record is typically used to indicate that you have eaten a snack in response to a low, and indicate how much sugar you ate.

This can be use by clients to visually show your lows and provide visual cues that blood glucose is eventually expected to rise.

### Episodes

An *episode* is used to convey a state, without providing a blood glucose measurement.

Episodes can be one of:

- `unknown`: when no value is known (can be used when you don't have a sensor)
- `disconnected`: when the sensor is disconnected (e.g. out of reach of Bluetooth)
- `error`: when an error occured
- `low`: when blood glucose is *low*
- `normal`: when blood glucose is in range
- `high`: when blood glucose is *high*

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
