# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Set the PORT environment variable.
ENV PORT=8026

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the application files
COPY . .

# Expose the port the container will listen on
EXPOSE 8026

# Run the server using uvicorn directly.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8026"]