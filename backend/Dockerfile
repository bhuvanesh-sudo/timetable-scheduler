# backend/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 1. Install system tools
RUN apt-get update && apt-get install -y gcc libpq-dev

# 2. COPY the requirements file from your laptop into the container
COPY requirements.txt /app/

# 3. Install the items on the list
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the code
COPY . /app/

# 5. Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]