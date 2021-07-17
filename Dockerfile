# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

ENV DISCORD_TOKEN=""
ENV DISCORD_GUILD=""
ENV TENDENCI_URI=""
ENV TENDENCI_API_KEY=""
ENV TENDENCI_API_USER=""

WORKDIR /app
RUN pip3 install -r requirements.txt
COPY . .
CMD ["./mbot.py"]
