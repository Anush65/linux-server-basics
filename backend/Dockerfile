FROM python:3.12-slim

RUN useradd -m appuser
WORKDIR /app

COPY app.py .

RUN pip install flask

USER appuser
EXPOSE 5000

CMD ["python", "app.py"]
