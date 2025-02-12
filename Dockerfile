ARG BASE_IMAGE=python:3.8-slim-buster
FROM $BASE_IMAGE
RUN apt-get -qqy update && \
    apt-get install --no-install-recommends -qqy build-essential libev-dev && \
    rm -rf /var/lib/apt/lists/*

COPY conf/ /exporter/conf/
COPY druid_exporter/ /exporter/druid_exporter/
COPY setup.py /exporter/setup.py

WORKDIR /exporter

RUN python ./setup.py install

EXPOSE 8000

ENTRYPOINT ["python", "-u", "druid_exporter/exporter.py"]
