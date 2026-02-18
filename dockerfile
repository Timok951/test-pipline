FROM python:latest

RUN apt-get update 

WORKDIR /app

COPY requirments.txt .

RUN pip install -r requirments.txt

COPY . .

ENV PROMETHEUS_MULTIPROC_DIR=/app/metrics_data

RUN mkdir -p /app/metrics_data

EXPOSE 8000

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
