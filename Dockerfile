FROM python:3.11-slim
WORKDIR /app
COPY requirements_pdf_service.txt .
RUN pip install -r requirements_pdf_service.txt
COPY . .
CMD gunicorn genome_pdf_service:app --bind 0.0.0.0:$PORT
