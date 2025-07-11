# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and to run in unbuffered mode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a secure, non-root system user with a non-login shell
RUN useradd --system --create-home --shell /bin/nologin --user-group appuser

# Use a virtual environment for better isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install dependencies into the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container at /app
COPY --chown=appuser:appuser . /app/

# Ensure the data directory exists and that files have correct permissions *before* switching user
# (The VOLUME instruction itself doesn't create the directory)
# Adjust data directory as needed for your application
RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Make port 8000 available (adjust if your application uses a different port)
EXPOSE 8000

# Define environment variables (can be overridden at runtime)
# Adjust these to your application's needs
ENV PYTHONPATH=/app

# Command to run the application (adjust to your application's entrypoint)
# This is an example, replace with how your application is started
CMD ["python", "whoistel.py"]
