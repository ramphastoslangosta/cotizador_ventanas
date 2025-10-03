# Dockerfile para Sistema de Cotización de Ventanas v5.0.0-RESILIENT
# Optimizado para entorno beta con seguridad empresarial

FROM python:3.11-slim

# Metadatos de la imagen
LABEL maintainer="Sistema de Cotización de Ventanas"
LABEL version="5.0.0-RESILIENT"
LABEL description="FastAPI window quotation system for Mexico SME market"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependencias del sistema incluyendo WeasyPrint requirements
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-xlib-2.0-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# === DEVOPS-20251001-001: Clear Python bytecode cache ===
# Prevents stale .pyc files from causing deployment issues
RUN echo "=== Clearing Python cache ===" && \
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete 2>/dev/null || true && \
    echo "✅ Python cache cleared"

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/static/uploads /app/backups \
    && chown -R appuser:appuser /app

# Establecer permisos correctos
RUN chmod +x scripts/*.sh || true

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]