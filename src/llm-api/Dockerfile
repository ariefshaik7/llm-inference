
FROM python:3.11-slim

WORKDIR /app

COPY src/llm-api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/llm-api/main.py /app/main.py
COPY src/llm-api/database.py /app/database.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]