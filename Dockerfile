FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN mkdir -p /app/logs \
    && touch /app/logs/app.log \
    && chmod -R 755 /app/logs


RUN rm -f /app/credentials/*.json || true

RUN useradd --create-home --shell /bin/bash botuser || true
USER botuser

ENV PATH="/home/botuser/.local/bin:${PATH}"

CMD ["python", "main.py"]
