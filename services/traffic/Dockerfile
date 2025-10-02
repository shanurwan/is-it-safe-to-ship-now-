FROM python:3.11-slim
WORKDIR /app
RUN pip install httpx==0.27.0
COPY gen.py .
CMD ["python", "gen.py"]
