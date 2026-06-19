FROM python:3.12-slim

WORKDIR /app

# gcc/g++ needed to compile any C extensions; curl used by the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# chroma_db is mounted at runtime — don't bake a stale copy into the image
RUN rm -rf /app/chroma_db
