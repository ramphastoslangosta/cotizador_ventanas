# Plan de Despliegue Beta - Sistema de Cotización de Ventanas

**Fecha:** 31 de Julio, 2025  
**Versión:** v5.0.0-RESILIENT  
**Estado:** ✅ **LISTO PARA BETA**  
**Objetivo:** Despliegue controlado con primeros usuarios beta

---

## 🎯 Resumen Ejecutivo

El sistema está **PRODUCTION READY** con seguridad empresarial, manejo de errores robusto y protección de datos GDPR-compliant. Este plan detalla el despliegue seguro para pruebas beta con usuarios reales en el mercado SME de México.

**Duración Estimada del Beta:** 4-6 semanas  
**Usuarios Beta Objetivo:** 5-10 empresas de ventanas medianas  
**Criterio de Éxito:** 95% uptime, 0 incidentes de seguridad, feedback positivo

---

## 📋 Fase 1: Preparación del Entorno Beta (Semana 1)

### 🔧 1.1 Configuración del Servidor

**Proveedor Recomendado:** DigitalOcean/AWS/Google Cloud
- **Instancia:** 2 CPU, 4GB RAM, 40GB SSD
- **SO:** Ubuntu 22.04 LTS
- **Dominio:** `beta-cotizador.tudominio.com`

**Configuración de Seguridad:**
```bash
# Firewall básico
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Actualizaciones automáticas
apt update && apt upgrade -y
apt install unattended-upgrades
```

### 🗄️ 1.2 Base de Datos

**PostgreSQL 15+ Configurado:**
- Database: `ventanas_beta_db`
- Backup automático cada 6 horas
- Retención: 30 días
- SSL requerido para conexiones

### 🔐 1.3 Variables de Entorno

**Archivo `.env` para Beta:**
```bash
# CONFIGURACIÓN BETA
DATABASE_URL="postgresql://usuario:password_seguro@localhost:5432/ventanas_beta_db"
SECRET_KEY="[generado-aleatoriamente-64-caracteres]"
SESSION_EXPIRE_HOURS=8
DEBUG=false
APP_NAME="Sistema de Cotización de Ventanas - BETA"

# CONFIGURACIÓN DE DOMINIO
ALLOWED_ORIGINS="https://beta-cotizador.tudominio.com"
COOKIE_SECURE=true
COOKIE_SAMESITE="strict"

# LÍMITES BETA
RATE_LIMIT_PER_MINUTE=150
MAX_BETA_USERS=50
```

### 🚀 1.4 Despliegue con Docker

**Dockerfile optimizado:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml para beta:**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ventanas_beta_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt

volumes:
  postgres_data:
  redis_data:
```

---

## 👥 Fase 2: Selección y Onboarding de Usuarios Beta (Semana 2)

### 🎯 2.1 Criterios de Selección de Beta Users

**Perfil Ideal:**
- Empresas de ventanas con 5-50 empleados
- Experiencia con software básico (Excel, email)
- Volumen: 20-100 cotizaciones/mes
- Ubicación: México (3-5 ciudades diferentes)
- Dispuestos a dar feedback estructurado

**Incentivos para Beta Users:**
- Acceso gratuito durante 3 meses
- Soporte prioritario vía WhatsApp/email
- Capacitación personalizada (1 hora)
- Influencia directa en desarrollo de features

### 📚 2.2 Proceso de Onboarding

**Semana 2.1: Inscripción y Setup**
1. **Formulario de Beta Application** (Google Forms)
2. **Entrevista de 30 min** (videollamada)
3. **Creación de cuenta empresarial**
4. **Configuración inicial de materiales y productos**

**Semana 2.2: Capacitación**
1. **Sesión de demostración** (1 hora por empresa)
2. **Entrega de manual de usuario**
3. **Setup de datos iniciales** (materiales, precios)
4. **Primera cotización guiada**

### 📖 2.3 Materiales de Capacitación

**Manual de Usuario Beta (PDF):**
- Guía de login y navegación
- Creación de catálogo de materiales
- Proceso de cotización paso a paso
- Generación de PDFs
- FAQ y troubleshooting

**Videos de Capacitación (5-10 min c/u):**
- Tour del sistema
- Crear primera cotización
- Gestión de materiales
- Personalización de empresa

---

## 📊 Fase 3: Monitoreo y Feedback (Semanas 3-6)

### 🔍 3.1 Sistema de Monitoreo

**Métricas Técnicas (Automáticas):**
```python
# Integración con el sistema existente
- Uptime: >99% objetivo
- Response time: <500ms promedio
- Error rate: <0.1%
- Database performance
- Security incidents: 0
```

**Métricas de Negocio:**
- Cotizaciones creadas por empresa/semana
- Tiempo promedio por cotización
- Features más/menos usadas
- Casos de error reportados por usuarios

### 📝 3.2 Recolección de Feedback

**Feedback Semanal Estructurado:**
```
1. ¿Qué funcionó bien esta semana?
2. ¿Qué problemas encontraste? (específicos)
3. ¿Qué feature te gustaría que mejoráramos primero?
4. Escala 1-10: ¿Recomendarías el sistema?
5. ¿Tiempo ahorrado vs método anterior?
```

**Canales de Feedback:**
- **Urgente:** WhatsApp directo (respuesta <2 horas)
- **Normal:** Email semanal
- **Sugerencias:** Form web integrado en el sistema

### 🚨 3.3 Alertas y Respuesta

**Sistema de Alertas Automáticas:**
- Error rate >1%: Alerta inmediata
- Downtime >5 min: Notificación SMS
- Usuario bloqueado: Investigación automática
- Database issues: Escalación técnica

**Protocolo de Respuesta:**
- **P1 (Sistema caído):** <30 min respuesta
- **P2 (Error funcional):** <2 horas respuesta  
- **P3 (Mejora UX):** <24 horas respuesta
- **P4 (Feature request):** Revisión semanal

---

## 🔄 Fase 4: Deployment Scripts y Automatización

### 🚀 4.1 Script de Despliegue Automatizado

**deploy-beta.sh:**
```bash
#!/bin/bash
set -e

echo "🚀 Iniciando despliegue beta..."

# Backup antes del despliegue
docker exec postgres pg_dump ventanas_beta_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Pull código actualizado
git pull origin main

# Build y deploy
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Health check
sleep 30
curl -f http://localhost:8000/health || exit 1

# Notificar éxito
echo "✅ Despliegue beta completado exitosamente"
```

### 📊 4.2 Script de Monitoreo

**monitor-beta.sh:**
```bash
#!/bin/bash

# Health checks cada 5 minutos
while true; do
    if ! curl -sf http://localhost:8000/health > /dev/null; then
        echo "🚨 ALERTA: Sistema no responde $(date)"
        # Enviar notificación (Slack/email/SMS)
    fi
    sleep 300
done
```

---

## 🆘 Fase 5: Plan de Rollback y Disaster Recovery

### ⏪ 5.1 Rollback Procedure

**En caso de problemas críticos:**
```bash
# 1. Detener servicio actual
docker-compose down

# 2. Restaurar backup de BD
psql ventanas_beta_db < backup_ultimo_estable.sql

# 3. Volver a versión anterior
git checkout [commit-estable]
docker-compose up -d

# 4. Notificar a usuarios beta
```

**Tiempo estimado de rollback:** <15 minutos

### 💾 5.2 Backups y Recovery

**Estrategia de Backups:**
- **Database:** Cada 6 horas + antes de cada deploy
- **Código:** Git con tags por versión
- **Configuración:** Versionado en repositorio privado
- **Logs:** Retención 30 días con rotación automática

**Recovery Testing:**
- Simulacro mensual de restore completo
- Documentación paso a paso actualizada

---

## 📋 Checklist Final Pre-Lanzamiento

### ✅ Técnico
- [ ] Servidor configurado y securizado
- [ ] Base de datos con backups automáticos  
- [ ] SSL/HTTPS configurado correctamente
- [ ] Monitoreo y alertas funcionando
- [ ] Scripts de deployment probados
- [ ] Plan de rollback documentado y probado

### ✅ Usuarios
- [ ] 5-10 empresas beta seleccionadas
- [ ] Materiales de capacitación creados
- [ ] Sesiones de onboarding programadas
- [ ] Canales de soporte establecidos
- [ ] Formularios de feedback preparados

### ✅ Proceso
- [ ] Cronograma de 6 semanas definido
- [ ] Responsabilidades asignadas
- [ ] Métricas de éxito definidas
- [ ] Plan de comunicación con betas
- [ ] Criterios para pasar a producción

---

## 🎯 Criterios de Éxito para Pasar a Producción

**Métricas Objetivo:**
- **Uptime:** >99.5% durante las 6 semanas
- **User Satisfaction:** Promedio >8/10
- **Error Rate:** <0.5% de requests
- **Security Incidents:** 0
- **Retention:** >80% de beta users continúan usando

**Condiciones para Graduación:**
- Al menos 3 empresas confirman ahorro de tiempo >50%
- 0 incidentes críticos en últimas 2 semanas
- Feedback features implementadas y probadas
- Proceso de soporte escalable definido

---

**Estado:** ✅ **READY TO EXECUTE**  
**Siguiente Paso:** Aprobar plan y comenzar preparación del servidor

---

*Este plan asegura un despliegue beta controlado y exitoso, minimizando riesgos mientras maximiza el aprendizaje de usuarios reales.*