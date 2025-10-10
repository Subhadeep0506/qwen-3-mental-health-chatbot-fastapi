FROM python:3.12.11-slim
COPY . /app
WORKDIR /app
# RUN apt-get update && apt-get install build-essential -y \
#     && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools --no-cache-dir
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080 5432
CMD ["uvicorn", "main:app", "--port", "8080"]