# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables to prevent Python from writing .pyc files and to run in unbuffered mode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a secure, non-root system user with a non-login shell
RUN useradd --system --create-home --shell /bin/nologin --user-group appuser

# Use a virtual environment for better isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies required for data processing
RUN apt-get update && apt-get install -y --no-install-recommends wget && rm -rf /var/lib/apt/lists/*


# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt first for better layer caching.
# pandas and xlrd are kept for future in-container DB updates via updatearcep.sh.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary application scripts.
# These are needed for the application to run and for future in-container DB updates.
# requirements.txt is already in WORKDIR /app from the previous COPY and used by pip install.
# updatearcep.sh uses `pip3 install -r requirements.txt` assuming it's in the current dir,
# so it needs to be in /app as well if updatearcep.sh's CWD is /app.
# The initial `COPY requirements.txt .` (where . is /app) handled this.
# Copy application files
COPY whoistel.py generatedb.py updatearcep.sh webapp.py history_manager.py query_op.py /app/
COPY static /app/static
COPY templates /app/templates

# Ensure updatearcep.sh is executable
RUN chmod +x /app/updatearcep.sh

# Run updatearcep.sh to download data and generate whoistel.sqlite3.
# This also creates the arcep/ directory with downloaded/converted data.
# This is done as root to ensure permissions for downloads and file creation.
# Set ENV to make updatearcep.sh skip its internal pip install.
ENV SKIP_PIP_INSTALL_IN_CONTAINER=true
RUN /app/updatearcep.sh

# Ensure the /app directory and its contents (including generated DB and arcep data)
# are owned by appuser. This is crucial before switching user.
# The /app/data directory is also created for potential future use (e.g., mounted volumes).
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port 5000 for Flask/Gunicorn
EXPOSE 5000

# Define environment variables (can be overridden at runtime)
ENV PYTHONPATH=/app


# ENTRYPOINT makes the container behave like an executable.
# CMD provides default arguments.
ENTRYPOINT ["gunicorn"]
CMD ["-w", "1", "-b", "0.0.0.0:5000", "webapp:app"]
