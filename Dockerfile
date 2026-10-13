
# 1. Start with Python 3.11.
FROM python:3.11-slim

# 2. Set the working directory inside the image.
WORKDIR /app

# 3. Configure Python's runtime behavior.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Copy the dependency list into the image.
COPY requirements.txt .

# 5. Install PyZMQ inside the image.
RUN python -m pip install --no-cache-dir -r requirements.txt

# 6. Copy the application source files.
COPY messages.py distributor.py worker.py collector.py ./
