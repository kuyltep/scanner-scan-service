# Base stage with all dependencies
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 \
    PATH=$PATH:/usr/lib/jvm/java-11-openjdk-amd64/bin \
    TMPDIR=/home/scanner/app/tmp

# Install system dependencies
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk build-essential curl wget unzip git bash \
                       glib2.0-dev pango1.0-dev libcairo2-dev libgdk-pixbuf2.0-dev \
                       libxml2-dev libxslt-dev \
                       gobject-introspection libffi-dev \
                       fontconfig ttf-dejavu ttf-liberation \
                       p7zip-full \
                       aapt || true && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -g 1000 scanner && \
    useradd -r -u 1000 -g scanner -m -d /home/scanner -s /bin/bash scanner

WORKDIR /home/scanner/app

# Copy and install smaliflow first (needed by VulnApk)
COPY smaliflow/ ./smaliflow/
RUN pip install --no-cache-dir -e ./smaliflow

# Copy requirements and install core dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install PDF generation libraries
RUN pip install --no-cache-dir weasyprint pdfkit jinja2

# Copy VulnApk tools and install its dependencies
COPY vulnapk/ ./vulnapk/
RUN chmod +x vulnapk/apkd* && \
    chmod 644 vulnapk/apkeditor.jar

# Install VulnApk deps
RUN pip install --no-cache-dir beautifulsoup4==4.13.4 \
                               charset-normalizer==3.4.2 \
                               colorama==0.4.6 \
                               lxml==5.4.0 \
                               more-itertools==10.7.0 \
                               soupsieve==2.7 \
                               tqdm==4.67.1 \
                               typing_extensions==4.13.2

# Copy app code
COPY --chown=scanner:scanner app_types/ ./app_types/
COPY --chown=scanner:scanner consumers/ ./consumers/
COPY --chown=scanner:scanner producers/ ./producers/
COPY --chown=scanner:scanner services/ ./services/
COPY --chown=scanner:scanner config/ ./config/
COPY --chown=scanner:scanner scanner/ ./scanner/
COPY --chown=scanner:scanner main.py ./

# Copy HTML template for reports
COPY report_template.html ./

# Create necessary directories
RUN mkdir -p tmp/vulnapk reports logs && \
    chown -R scanner:scanner /home/scanner/app

# Fallback scan.json
RUN echo '[]' > /home/scanner/app/scan.json

# Switch to scanner user
USER scanner

# Test imports to verify everything works
RUN python -c "from scanner.scanner import Scanner; from app_types.message_types import IncomingMessage; print('All imports successful!')"

# Expose port (if needed for future HTTP API)
EXPOSE 8000

# Default command
CMD ["python", "main.py"]
