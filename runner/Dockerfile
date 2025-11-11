FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY runner/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY runner/service.py service.py

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8001"]
