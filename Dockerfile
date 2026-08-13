FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY src/ src/
COPY ml/ ml/
COPY orchestration/ orchestration/
COPY warehouse/ warehouse/
COPY data/source/ data/source/
COPY reports/ reports/
COPY pyproject.toml .

EXPOSE 8000

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
