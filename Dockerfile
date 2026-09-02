FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 --retries=10 \
    torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --timeout=120 --retries=10 -r requirements.txt

COPY project ./project
COPY assets ./assets
COPY markdown_docs ./markdown_docs
COPY parent_store ./parent_store

EXPOSE 7860

CMD ["python", "project/app.py"]
