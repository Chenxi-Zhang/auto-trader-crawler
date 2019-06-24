FROM python:3.7.1

COPY requirements.txt /
RUN cd / && \
    pip install -r requirements.txt

VOLUME /data
