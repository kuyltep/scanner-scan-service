# Multi-stage build for optimized production image
FROM python:alpine as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk \
    PATH=$PATH:/usr/lib/jvm/java-11-openjdk/bin

# Install system dependencies
RUN apk update && apk add --no-cache \
    # Java for APK decompilation
    openjdk11-jdk \
    # Build tools and utilities
    build-base \
    curl \
    wget \
    unzip \
    git \
    bash \
    # WeasyPrint dependencies
    glib-dev \
    pango-dev \
    cairo-dev \
    gdk-pixbuf-dev \
    libffi-dev \
    gobject-introspection-dev \
    # Fonts for PDF generation
    fontconfig \
    ttf-dejavu \
    ttf-liberation \
    # Additional Alpine dependencies
    musl-dev \
    linux-headers \
    # XML processing libraries
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/cache/apk/*

# Verify Java installation
RUN java -version && javac -version

# Create application user (Alpine way)
RUN addgroup -g 1000 scanner && \
    adduser -D -s /bin/bash -u 1000 -G scanner scanner
WORKDIR /home/scanner/app

# Copy and install smaliflow first (needed by VulnApk)
COPY smaliflow/ ./smaliflow/
RUN cd smaliflow && pip install --no-cache-dir -e .

# Copy requirements and install core dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install PDF generation libraries
RUN pip install --no-cache-dir weasyprint pdfkit jinja2

# Copy VulnApk tools and install its dependencies
COPY vulnapk/ ./vulnapk/
RUN chmod +x vulnapk/apkd vulnapk/apkd.exe && \
    chmod 644 vulnapk/apkeditor.jar && \
    # Install VulnApk requirements (excluding the problematic smaliflow line)
    pip install --no-cache-dir beautifulsoup4==4.13.4 \
                               charset-normalizer==3.4.2 \
                               colorama==0.4.6 \
                               lxml==5.4.0 \
                               more-itertools==10.7.0 \
                               soupsieve==2.7 \
                               tqdm==4.67.1 \
                               typing_extensions==4.13.2

# Create necessary directories
RUN mkdir -p tmp/vulnapk reports logs && \
    chown -R scanner:scanner /home/scanner/app

# Copy application code
COPY --chown=scanner:scanner app_types/ ./app_types/
COPY --chown=scanner:scanner consumers/ ./consumers/
COPY --chown=scanner:scanner producers/ ./producers/
COPY --chown=scanner:scanner services/ ./services/
COPY --chown=scanner:scanner config/ ./config/
COPY --chown=scanner:scanner scanner/ ./scanner/
COPY --chown=scanner:scanner main.py ./

# Copy HTML template for reports
COPY report_template.html ./

# Create scan.json if it doesn't exist (fallback data)
RUN echo '[]' > scan.json

# Create environment file template
RUN echo "# Environment variables for scanner service" > .env.template && \
    echo "KAFKA_HOST=localhost:9092" >> .env.template && \
    echo "KAFKA_RECIEVE_TOPIC=scan-requests" >> .env.template && \
    echo "KAFKA_SEND_TOPIC=scan-results" >> .env.template && \
    echo "KAFKA_GROUP_ID=scanner-group" >> .env.template && \
    echo "MINIO_ENDPOINT=localhost:9000" >> .env.template && \
    echo "MINIO_ACCESS_KEY=minioadmin" >> .env.template && \
    echo "MINIO_SECRET_KEY=minioadmin" >> .env.template && \
    echo "MINIO_BUCKET_SCANS=scans" >> .env.template && \
    echo "MINIO_BUCKET_RESULTS=results" >> .env.template

# Switch to application user
USER scanner

# Test imports to verify everything works
RUN python -c "from scanner.scanner import Scanner; from app_types.message_types import IncomingMessage; print('All imports successful!')"

# Expose port (if needed for future HTTP API)
EXPOSE 8000

# Default command
CMD ["python", "main.py"]