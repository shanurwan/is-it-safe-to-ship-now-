FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi==0.114.2 uvicorn==0.30.6 pyyaml==6.0.2
COPY server.py .
EXPOSE 9099
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","9099"]