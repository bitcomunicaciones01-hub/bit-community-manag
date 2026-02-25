# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# ffmpeg: for video processing (TikTok/Reels)
# libsm6, libxext6: for OpenCV (if used by any image lib)
# git: sometimes needed for pip install from git
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8501 for Streamlit Dashboard
EXPOSE 8501

# Run the application
# We run main.py which starts the scheduler, and it also launches Streamlit as a subprocess
CMD ["python", "main_server.py"]
