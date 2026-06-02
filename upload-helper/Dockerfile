FROM python:3.11-slim
WORKDIR /app
COPY server.py .
RUN pip install --no-cache-dir requests
EXPOSE 8888
CMD ["python", "server.py"]
