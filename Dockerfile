# syntax=docker/dockerfile:1
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Install ping
RUN apt-get update && apt-get -y install iputils-ping

# Change working directory to /app
WORKDIR /app

COPY requirements.txt requirements.txt
COPY main.py auth0.py ./
COPY pingc/ ./pingc/
COPY .env ./

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
