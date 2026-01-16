
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

# We don't set an ENTRYPOINT here because the Vertex AI Pipeline can override it, 
# or we can set it to run the training script by default.
# But keeping it flexible is good.
