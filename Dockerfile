FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install flask reportlab Pillow gunicorn requests
CMD gunicorn genome_pdf_service:app --bind 0.0.0.0:$PORT
