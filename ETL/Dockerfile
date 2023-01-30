# syntax=docker/dockerfile:1

FROM python:3.10.8

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "app.py", "kafka:9092", "prometheusdata"]