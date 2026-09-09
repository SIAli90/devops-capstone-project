FROM python:3.9-slim

# Create the application working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary application files into the image
COPY . /app

# Switch to a non-root user before running the service
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia

# Expose the application port and run the Accounts service
EXPOSE 8080
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]
