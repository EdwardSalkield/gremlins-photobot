# gremlins-photobot docker image

FROM alpine:3.10
LABEL description="gremlins-photobot docker image." maintainer="Edd Salkield"

# Install dependencies
RUN apk add --no-cache python3
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install flask datetime werkzeug exif configparser
ADD src/ /gremlins-photobot/

EXPOSE 8080

CMD python3 /gremlins-photobot/server.py
