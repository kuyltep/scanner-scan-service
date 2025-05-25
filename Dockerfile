# Multi-stage build for optimized production image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 \
    PATH=$PATH:/usr/lib/jvm/java-11-openjdk-amd64/bin

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Java for APK decompilation
    openjdk-11-jdk \
    # wkhtmltopdf for PDF generation
    wkhtmltopdf \
    xvfb \
    # Build tools and utilities
    build-essential \
    curl \
    wget \
    unzip \
    git \
    # Fonts for PDF generation
    fonts-liberation \
    fonts-dejavu-core \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Java installation
RUN java -version && javac -version

# Create application user
RUN useradd --create-home --shell /bin/bash scanner
WORKDIR /home/scanner/app

# Copy requirements first for better caching
COPY requirements.txt ./
COPY vulnapk/requirements.txt ./vulnapk_requirements.txt
COPY vulnapk/service_requirements.txt ./service_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r vulnapk_requirements.txt && \
    pip install --no-cache-dir -r service_requirements.txt

# Copy VulnApk tools and dependencies
COPY vulnapk/ ./vulnapk/
RUN chmod +x vulnapk/apkd vulnapk/apkd.exe && \
    chmod 644 vulnapk/apkeditor.jar

# Create necessary directories
RUN mkdir -p tmp/vulnapk reports logs && \
    chown -R scanner:scanner /home/scanner/app

# Copy application code
COPY --chown=scanner:scanner . .

# Copy HTML template for reports
COPY report_template.html ./

# Create scan.json if it doesn't exist (fallback data)
RUN echo '[]' > scan.json

# Set up wkhtmltopdf wrapper for headless operation
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf "$@"' > /usr/local/bin/wkhtmltopdf-headless && \
    chmod +x /usr/local/bin/wkhtmltopdf-headless

# Switch to application user
USER scanner


# Expose port (if needed for future HTTP API)
EXPOSE 8000

# Default command
CMD ["python", "main.py"]