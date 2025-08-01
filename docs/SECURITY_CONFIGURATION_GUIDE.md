# Guía de Configuración de Seguridad para Producción

**Sistema de Cotización de Ventanas v5.0.0-SECURE**  
*Enterprise-Grade Security Configuration Guide*

## 🎯 Resumen Ejecutivo

Esta guía proporciona las configuraciones específicas necesarias para desplegar el sistema de cotización de ventanas con **seguridad de nivel empresarial** en un entorno de producción para el mercado SME de México.

**Estado de Seguridad**: ✅ **PRODUCTION READY** (Milestone 1.1 completado)

---

## 📋 Checklist Pre-Despliegue

### ✅ Completado (Milestone 1.1)
- [x] Evaluación segura de fórmulas (SafeFormulaEvaluator)
- [x] Validación comprensiva de entradas (InputValidator + bleach)
- [x] Protección CSRF con tokens
- [x] Configuración segura de cookies (HttpOnly, SameSite)
- [x] CORS restrictivo para dominios específicos
- [x] Rate limiting (100 req/min por IP)
- [x] Protección contra fuerza bruta (bloqueo de cuenta)
- [x] Requisitos de contraseñas fuertes
- [x] Headers de seguridad automáticos

### 🔧 Configuraciones Pendientes para Producción
- [ ] Variables de entorno de producción
- [ ] Certificados SSL/TLS
- [ ] Configuración HTTPS
- [ ] Rate limiting con Redis
- [ ] Logging y monitoreo
- [ ] Respaldos de base de datos
- [ ] Configuración de firewall

---

## 🔐 Configuración de Variables de Entorno

### Archivo `.env` para Producción

```bash
# ===========================================
# CONFIGURACIÓN DE PRODUCCIÓN - CRÍTICA
# ===========================================

# === BASE DE DATOS ===
DATABASE_URL="postgresql://username:secure_password@your-db-host:5432/ventanas_db"

# === SEGURIDAD ===
SECRET_KEY="your-super-secure-256-bit-secret-key-change-this-in-production"
SESSION_EXPIRE_HOURS=2

# === APLICACIÓN ===
APP_NAME="Sistema de Cotización de Ventanas"
DEBUG=False

# === CONFIGURACIÓN DE NEGOCIO ===
DEFAULT_PROFIT_MARGIN=0.25
DEFAULT_INDIRECT_COSTS=0.15
DEFAULT_TAX_RATE=0.16

# === SUPABASE (si se usa) ===
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-supabase-anon-key"

# === CONFIGURACIÓN ADICIONAL DE SEGURIDAD ===
ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

### Configuración de `config.py` para Producción

```python
# config.py - Configuración para producción
from pydantic_settings import BaseSettings
from typing import List
import os

class ProductionSettings(BaseSettings):
    # Database
    database_url: str
    
    # Security
    secret_key: str
    session_expire_hours: int = 2
    
    # Application
    app_name: str = "Sistema de Cotización de Ventanas"
    debug: bool = False
    
    # CORS Configuration - PRODUCTION
    allowed_origins: List[str] = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        # Agregar dominios específicos de producción
    ]
    
    # Security Settings - PRODUCTION
    cookie_secure: bool = True  # HTTPS only
    cookie_samesite: str = "strict"  # Strict CSRF protection
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Business defaults
    default_profit_margin: float = 0.25
    default_indirect_costs: float = 0.15
    default_tax_rate: float = 0.16
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = ProductionSettings()
```

---

## 🛡️ Configuración de Seguridad Avanzada

### 1. HTTPS y Certificados SSL

#### Opción A: Let's Encrypt (Gratuito)
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Configurar renovación automática
sudo crontab -e
# Agregar: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Opción B: Certificado Comercial
```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Configuración de seguridad SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Configuración de Base de Datos Segura

#### PostgreSQL Security Hardening
```sql
-- Crear usuario específico para la aplicación
CREATE USER ventanas_app WITH PASSWORD 'secure_random_password_here';

-- Crear base de datos
CREATE DATABASE ventanas_db OWNER ventanas_app;

-- Asignar permisos mínimos necesarios
GRANT CONNECT ON DATABASE ventanas_db TO ventanas_app;
GRANT USAGE ON SCHEMA public TO ventanas_app;
GRANT CREATE ON SCHEMA public TO ventanas_app;
```

#### Configuración de `postgresql.conf`
```bash
# Configuraciones de seguridad en PostgreSQL
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'

# Logging para auditoría
log_connections = on
log_disconnections = on
log_statement = 'mod'  # Log INSERT, UPDATE, DELETE
```

### 3. Rate Limiting con Redis (Opcional - Escalabilidad)

```python
# security/redis_rate_limiter.py - Para entornos de alta demanda
import redis
import time
from typing import Optional

class RedisRateLimiter:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
    
    def is_allowed(self, key: str, limit: int = 100, window: int = 60) -> bool:
        current_time = int(time.time())
        window_start = current_time - window
        
        # Limpiar entradas antiguas
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Contar solicitudes en la ventana actual
        current_requests = self.redis_client.zcard(key)
        
        if current_requests >= limit:
            return False
        
        # Agregar solicitud actual
        self.redis_client.zadd(key, {str(current_time): current_time})
        self.redis_client.expire(key, window)
        
        return True
```

---

## 🔍 Monitoreo y Logging

### Configuración de Logging de Seguridad

```python
# logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_security_logging():
    # Logger de seguridad
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    
    # Handler para archivo de seguridad
    security_handler = RotatingFileHandler(
        'logs/security.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Formato de log de seguridad
    security_format = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    )
    security_handler.setFormatter(security_format)
    security_logger.addHandler(security_handler)
    
    return security_logger

# Usar en middleware de seguridad
security_logger = setup_security_logging()
```

### Métricas de Seguridad a Monitorear

1. **Intentos de Login Fallidos**
   - Umbral: >5 intentos desde la misma IP en 5 minutos
   - Acción: Alertar y considerar bloqueo temporal

2. **Violaciones de Rate Limiting**
   - Umbral: >100 requests/minuto por IP
   - Acción: Bloqueo automático y log de seguridad

3. **Intentos de Evaluación de Fórmulas Maliciosas**
   - Detectar patrones sospechosos en fórmulas
   - Log inmediato para análisis

4. **Errores de Validación de CSRF**
   - Monitorear tokens CSRF inválidos
   - Posible indicador de ataque

---

## 🚨 Plan de Respuesta a Incidentes

### Procedimiento de Emergencia

#### 1. Detección de Ataque
```bash
# Comandos de emergencia para monitoreo
tail -f logs/security.log | grep "CRITICAL"
netstat -an | grep :8000
ss -tulpn | grep :8000
```

#### 2. Bloqueo Inmediato
```bash
# Bloquear IP específica con iptables
sudo iptables -A INPUT -s MALICIOUS_IP -j DROP

# Reiniciar aplicación si es necesario
sudo systemctl restart ventanas-app
```

#### 3. Análisis Post-Incidente
1. Revisar logs de seguridad: `logs/security.log`
2. Verificar base de datos: buscar modificaciones sospechosas
3. Comprobar integridad de archivos del sistema
4. Actualizar reglas de seguridad según sea necesario

---

## 🔧 Configuración de Firewall

### UFW (Ubuntu Firewall)
```bash
# Configuración básica de firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH (cambiar puerto si no es 22)
sudo ufw allow ssh

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Permitir PostgreSQL solo desde aplicación
sudo ufw allow from YOUR_APP_SERVER_IP to any port 5432

# Activar firewall
sudo ufw enable
```

---

## 📊 Respaldos y Recuperación

### Respaldo Automático de Base de Datos
```bash
#!/bin/bash
# backup_db.sh - Script de respaldo automático

DB_NAME="ventanas_db"
DB_USER="ventanas_app"
BACKUP_DIR="/var/backups/ventanas"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Realizar respaldo
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Comprimir respaldo
gzip $BACKUP_DIR/backup_$DATE.sql

# Limpiar respaldos antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### Crontab para Respaldos Automáticos
```bash
# Editar crontab
crontab -e

# Agregar respaldo diario a las 2:00 AM
0 2 * * * /path/to/backup_db.sh >> /var/log/backup.log 2>&1
```

---

## 🎯 Validación Final de Seguridad

### Tests de Penetración Básicos

```bash
# 1. Test de Rate Limiting
for i in {1..150}; do
    curl -s "https://yourdomain.com/api/materials" &
done
# Debe bloquear después de 100 requests

# 2. Test de Headers de Seguridad
curl -I https://yourdomain.com
# Verificar presencia de X-Frame-Options, CSP, etc.

# 3. Test de HTTPS
curl -I http://yourdomain.com
# Debe redirigir a HTTPS

# 4. Test de CORS
curl -H "Origin: https://malicious-site.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://yourdomain.com/api/materials
# Debe rechazar origen no autorizado
```

---

## 📋 Checklist Final de Despliegue

- [ ] ✅ **Seguridad implementada**: Milestone 1.1 completado
- [ ] **Variables de entorno**: Configuradas para producción
- [ ] **Certificados SSL**: Instalados y configurados
- [ ] **HTTPS forzado**: Redirección HTTP → HTTPS
- [ ] **Firewall**: Configurado con reglas restrictivas
- [ ] **Base de datos**: Usuario con permisos mínimos
- [ ] **Respaldos**: Configurados y probados
- [ ] **Logging**: Sistema de logs de seguridad activo
- [ ] **Monitoreo**: Alertas configuradas
- [ ] **Tests de seguridad**: Ejecutados exitosamente

---

## 🆘 Contactos de Emergencia

**Administrador de Sistema**: [Tu información de contacto]  
**Responsable de Seguridad**: [Información de contacto]  
**Proveedor de Hosting**: [Información de soporte técnico]

---

**Estado**: ✅ **PRODUCTION READY** - Enterprise Grade Security  
**Última Actualización**: Julio 28, 2025  
**Próxima Revisión**: Antes del despliegue en producción