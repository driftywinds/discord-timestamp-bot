# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash botuser

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the bot script
COPY bot.py .

# Change ownership of the app directory to the bot user
RUN chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Run the bot
CMD ["python3", "bot.py"]