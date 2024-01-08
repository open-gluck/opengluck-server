FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY app/package.json app/package-lock.json* ./
RUN npm ci


FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./app/node_modules
COPY . .
RUN cd app && npm run build


FROM redis:7.0.9 as redis


FROM python:3.11.2-bullseye as app
COPY --from=redis /usr/local/bin/redis-server /usr/local/bin/redis-server
COPY --from=redis /usr/local/bin/redis-cli /usr/local/bin/redis-cli

RUN apt update && apt -y dist-upgrade && apt install -y supervisor nginx openssl nginx-extras
RUN apt-get update && apt-get install -y ca-certificates curl gnupg && mkdir -p /etc/apt/keyrings && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && NODE_MAJOR=20 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && apt-get update && apt-get install nodejs -y

RUN useradd -ms /bin/bash opengluck
RUN mkdir -p /opt && chown opengluck:opengluck /opt
RUN mkdir -p /var/log/nginx && touch /var/run/nginx.pid && chown -R opengluck:opengluck /var/log/nginx /var/lib/nginx /var/run/nginx.pid

COPY . /app
WORKDIR /app
RUN python -m venv /opt/venv
RUN bash -c "source /opt/venv/bin/activate && pip install -r requirements.txt && echo \"import opengluck.server; opengluck.server.check()\"|python"

EXPOSE 3000
EXPOSE 8080
CMD ./scripts/start

# Dev app

FROM app as app-dev
RUN mkdir -p /app/app/node_modules /app/data && chown opengluck:opengluck /app/app/node_modules /app/data
USER opengluck

# Standalone app

FROM app
COPY --from=builder --chown=opengluck:opengluck /app/app/node_modules/.next/standalone /app/app
COPY --from=builder --chown=opengluck:opengluck /app/app/node_modules/.next/static /app/app/node_modules/.next/static
RUN mkdir -p /app/data && chown opengluck:opengluck /app/data
USER opengluck
