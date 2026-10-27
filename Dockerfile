FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY web ./web
COPY data ./data
RUN useradd --create-home appuser && mkdir /app/runtime && chown appuser /app/runtime
USER appuser
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
