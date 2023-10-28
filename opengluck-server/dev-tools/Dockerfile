FROM redis:7.0.9 as redis

FROM python:3.11.2-bullseye
COPY --from=redis /usr/local/bin/redis-server /usr/local/bin/redis-server
COPY --from=redis /usr/local/bin/redis-cli /usr/local/bin/redis-cli

RUN apt update && apt -y dist-upgrade && apt install -y supervisor nginx openssl nginx-extras

# create the opengluck user
RUN useradd -ms /bin/bash opengluck
RUN mkdir -p /app && chown opengluck:opengluck /app
RUN mkdir -p /opt && chown opengluck:opengluck /opt

USER opengluck

RUN python -m venv /opt/venv

WORKDIR /app

# We stay up only to provide the environment over which to run the Python scripts,
# but we have nothing else to do
CMD sleep infinity
