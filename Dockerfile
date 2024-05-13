# Use the official Python image from the Docker Hub
FROM python:3.10-slim

RUN apt-get update
RUN pip install --upgrade pip

# Install dependencies required for mysqlclient
RUN apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config -y

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install the required dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
# COPY . .

# Set an environment variable to avoid unbuffered output in logs
ENV PYTHONUNBUFFERED=1

# Expose the port that Streamlit uses (8501 by default)
EXPOSE 8501

# Command to run the streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
