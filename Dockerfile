FROM python:3.7.1-alpine

RUN mkdir /workdir
COPY requirements.txt /workdir
COPY core /workdir/core
COPY setup.py /workdir
RUN cd /workdir && \
    pip install -r requirements.txt && \
    pip install -e .

WORKDIR /workdir/core
