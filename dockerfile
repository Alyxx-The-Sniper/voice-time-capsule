# Use an official Python image as a parent image
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg


# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables (optional, can also be set in Render)
# ENV FLASK_ENV=production

# Expose the port Flask runs on
EXPOSE 10000

# Command to run your app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
