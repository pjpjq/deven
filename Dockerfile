FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
ENV PYTHONUNBUFFERED=1 SQLITE_PATH=/data/deven.sqlite3
RUN mkdir -p /data
CMD ["python", "-m", "app.bot"]
