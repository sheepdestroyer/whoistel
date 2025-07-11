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

# Copy requirements.txt first for better layer caching.
# pandas and xlrd are kept for future in-container DB updates via updatearcep.sh.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary application scripts.
# These are needed for the application to run and for future in-container DB updates.
# Ensure requirements.txt is also in /app for updatearcep.sh if it invokes pip directly.
COPY whoistel.py xls_to_csv_converter.py generatedb.py updatearcep.sh requirements.txt /app/

# Ensure updatearcep.sh is executable
RUN chmod +x /app/updatearcep.sh

# Run updatearcep.sh to download data and generate whoistel.sqlite3.
# This also creates the arcep/ directory with downloaded/converted data.
# This is done as root to ensure permissions for downloads and file creation.
RUN /app/updatearcep.sh

# Ensure the /app directory and its contents (including generated DB and arcep data)
# are owned by appuser. This is crucial before switching user.
# The /app/data directory is also created for potential future use (e.g., mounted volumes).
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# EXPOSE 8000 is kept in preparation for future web service functionality.
EXPOSE 8000

# Define environment variables (can be overridden at runtime)
ENV PYTHONPATH=/app

# ENTRYPOINT makes the container behave like an executable.
# CMD provides default arguments (e.g., --help) if no arguments are given to `docker run`.
ENTRYPOINT ["python", "/app/whoistel.py"]
CMD ["--help"]
