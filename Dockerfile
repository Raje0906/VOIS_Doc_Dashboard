FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for reports if it doesn't exist
RUN mkdir -p static/reports

# Expose the port Hugging Face Spaces expects
EXPOSE 7860

# Run the application with Gunicorn
# Bind to 0.0.0.0:7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "doc_app:app"]
