# Lista de Verificación - Despliegue Beta

**Sistema de Cotización de Ventanas v5.0.0-RESILIENT**  
**Fecha de Despliegue:** _______________  
**Servidor IP:** _______________  
**Dominio:** _______________

---

## 📋 FASE 1: PREPARACIÓN DEL SERVIDOR

### ✅ Servidor Cloud
- [ ] **Proveedor seleccionado:** DigitalOcean / AWS / Google Cloud
- [ ] **Especificaciones:** 2 vCPUs, 4GB RAM, 80GB SSD mínimo
- [ ] **Sistema Operativo:** Ubuntu 22.04 LTS
- [ ] **IP Pública asignada:** _______________
- [ ] **SSH Key configurado**
- [ ] **Acceso SSH funcionando:** `ssh root@IP`

### ✅ Configuración Inicial
- [ ] **Sistema actualizado:** `apt update && apt upgrade -y`
- [ ] **Firewall configurado:** Puertos 22, 80, 443 abiertos
- [ ] **Docker instalado:** Verificar con `docker --version`
- [ ] **Docker Compose instalado:** Verificar con `docker-compose --version`
- [ ] **Usuario 'ventanas' creado** y agregado a grupo docker
- [ ] **SSH keys copiados** al usuario ventanas

**Script de configuración rápida:**
```bash
# Ejecutar como root
curl -fsSL https://raw.githubusercontent.com/tu-repo/scripts/quick-setup.sh | bash
```

---

## 📁 FASE 2: CÓDIGO Y CONFIGURACIÓN

### ✅ Repositorio y Archivos
- [ ] **Código clonado** en `/home/ventanas/app/`
- [ ] **Archivos esenciales presentes:**
  - [ ] `main.py`
  - [ ] `requirements.txt`
  - [ ] `docker-compose.beta.yml`
  - [ ] `scripts/deploy-beta.sh`
  - [ ] `.env.beta.template`

### ✅ Variables de Entorno
- [ ] **Archivo .env creado:** `cp .env.beta.template .env`
- [ ] **SECRET_KEY generado:** 64 caracteres aleatorios
- [ ] **DATABASE_URL configurado:**
  - Usuario: `ventanas_user`
  - Password: **[ANOTAR PASSWORD SEGURO]** _______________
  - Base: `ventanas_beta_db`
- [ ] **Dominio configurado:** `ALLOWED_ORIGINS="https://tu-dominio.com"`
- [ ] **Email de alertas:** `ALERT_EMAIL="tu-email@ejemplo.com"`

**Verificar configuración:**
```bash
cd ~/app
grep -E "SECRET_KEY|DATABASE_URL|ALLOWED_ORIGINS" .env
```

---

## 🌐 FASE 3: DOMINIO Y DNS

### ✅ Configuración DNS
- [ ] **Dominio registrado:** _______________
- [ ] **Subdominio elegido:** beta-cotizador.tudominio.com
- [ ] **Registro A creado:**
  - Nombre: `beta-cotizador`
  - Tipo: `A`
  - Valor: `[IP DEL SERVIDOR]`
  - TTL: `300`
- [ ] **Propagación DNS verificada:** `nslookup beta-cotizador.tudominio.com`

### ✅ Certificado SSL
- [ ] **Certbot instalado:** `sudo apt install certbot python3-certbot-nginx`
- [ ] **Nginx configurado** para el dominio
- [ ] **Certificado SSL obtenido:** `sudo certbot --nginx -d tu-dominio.com`
- [ ] **HTTPS funcionando:** Verificar en navegador sin warnings

**Verificar SSL:**
```bash
curl -I https://beta-cotizador.tudominio.com
# Debe retornar: HTTP/2 200
```

---

## 🐳 FASE 4: DESPLIEGUE DOCKER

### ✅ Preparación
- [ ] **Permisos del script:** `chmod +x scripts/deploy-beta.sh`
- [ ] **Directorio de backups creado:** `mkdir -p ~/backups`
- [ ] **Configuración final del .env:** Dominio HTTPS actualizado

### ✅ Primera Ejecución
- [ ] **Despliegue ejecutado:** `./scripts/deploy-beta.sh deploy`
- [ ] **Sin errores en el output**
- [ ] **Todos los containers corriendo:** `docker-compose ps`
- [ ] **Base de datos inicializada** correctamente

**Verificar containers:**
```bash
docker-compose -f docker-compose.beta.yml ps
# Todos deben mostrar "Up" status
```

---

## ✅ FASE 5: VERIFICACIÓN FUNCIONAL

### ✅ Conectividad Básica
- [ ] **Health check OK:** `curl https://tu-dominio.com/health`
- [ ] **Página de login carga** en navegador
- [ ] **Sin errores 500** en los logs
- [ ] **SSL certificate válido** (candado verde en navegador)

### ✅ Funcionalidad de Aplicación
- [ ] **Registro de usuario funciona**
- [ ] **Login exitoso**
- [ ] **Dashboard carga correctamente**
- [ ] **Configuración de empresa accesible**
- [ ] **Catálogo de materiales funciona**
- [ ] **Nueva cotización se puede crear**
- [ ] **PDF se genera correctamente**

**Test de funcionalidad completa:**
1. Registrar usuario: _______________
2. Configurar datos de empresa
3. Agregar 3-5 materiales básicos
4. Crear cotización de prueba
5. Generar PDF

---

## 📊 FASE 6: MONITOREO Y LOGS

### ✅ Sistema de Logs
- [ ] **Logs de aplicación visibles:** `docker-compose logs app`
- [ ] **Logs de base de datos OK:** `docker-compose logs postgres`
- [ ] **Logs estructurados** sin errores críticos
- [ ] **Rotación de logs configurada**

### ✅ Monitoreo
- [ ] **Health checks automáticos funcionando**
- [ ] **Script de monitoreo creado** y ejecutándose
- [ ] **Alertas por email configuradas**
- [ ] **Backup automático configurado**

**Verificar logs en tiempo real:**
```bash
docker-compose -f docker-compose.beta.yml logs -f --tail=20
```

---

## 💾 FASE 7: BACKUP Y RECOVERY

### ✅ Sistema de Backup
- [ ] **Script de backup creado:** `~/backup-daily.sh`
- [ ] **Backup manual ejecutado exitosamente**
- [ ] **Archivo de backup comprimido** y ubicado en `~/backups/`
- [ ] **Cron job configurado** para backup diario a las 2 AM
- [ ] **Política de retención:** 30 días de backups

### ✅ Test de Recovery
- [ ] **Proceso de rollback documentado**
- [ ] **Restore de backup probado** (en ambiente de test)
- [ ] **Script de rollback ejecutable**

**Test de backup:**
```bash
./backup-daily.sh
ls -la ~/backups/
# Debe mostrar archivo .sql.gz reciente
```

---

## 👥 FASE 8: PREPARACIÓN PARA USUARIOS

### ✅ Documentación
- [ ] **Manual de usuario impreso/enviado**
- [ ] **Datos de acceso preparados** para 5-10 usuarios beta
- [ ] **Formularios de feedback preparados**
- [ ] **Canal de soporte configurado** (WhatsApp/Email)

### ✅ Datos de Usuario de Prueba
- [ ] **Usuario admin creado:** _______________
- [ ] **Configuración básica completada**
- [ ] **Materiales de ejemplo cargados**
- [ ] **Cotización de demostración creada**

---

## 🔒 FASE 9: SEGURIDAD FINAL

### ✅ Checklist de Seguridad
- [ ] **Firewall activo:** `ufw status`
- [ ] **Fail2ban configurado** para SSH
- [ ] **Root login deshabilitado**
- [ ] **Password authentication deshabilitado**
- [ ] **SSL certificate válido y auto-renovable**
- [ ] **Headers de seguridad configurados**
- [ ] **CORS restrictivo configurado**

### ✅ Passwords y Secrets
- [ ] **Database password seguro** (8+ caracteres, números, símbolos)
- [ ] **SECRET_KEY único** y aleatorio
- [ ] **Passwords documentados** en lugar seguro
- [ ] **SSH keys respaldados**

---

## 📋 INFORMACIÓN FINAL PARA DOCUMENTAR

### 📊 Datos del Servidor
```
Proveedor: ____________________
IP Pública: ___________________
Dominio: ______________________
Usuario SSH: ventanas
Ubicación DC: _________________
Costo mensual: ________________
```

### 🔑 Credenciales Críticas
```
Database User: ventanas_user
Database Password: _______________
Admin Email: ____________________
Admin Password: _________________
Domain Registrar: _______________
SSL Provider: Let's Encrypt (auto)
```

### 📞 Contactos de Emergencia
```
Soporte Cloud Provider: _________
Soporte DNS/Dominio: ____________
Contacto Técnico: _______________
Email de Alertas: _______________
WhatsApp Soporte: _______________
```

---

## ✅ VERIFICACIÓN FINAL

### Antes de declarar "LISTO PARA BETA":
- [ ] **Todos los items anteriores completados**
- [ ] **Sistema funcionando por 24 horas sin errores**
- [ ] **Al menos 2 cotizaciones de prueba creadas**
- [ ] **Backup y restore probados**
- [ ] **Monitoreo reportando métricas sanas**
- [ ] **Plan de onboarding de usuarios preparado**

### Test Final de Usuario
- [ ] **Navegador incógnito:** Ir a la URL
- [ ] **Registro de usuario nuevo funciona**
- [ ] **Configuración completa de empresa**
- [ ] **Creación de cotización completa**
- [ ] **PDF descarga correctamente**
- [ ] **Sistema responde rápido** (<2 segundos)

---

## 🎯 DECLARACIÓN DE READY

**Fecha de completación:** _______________  
**Responsable del despliegue:** _______________  
**Próximo paso:** Comenzar onboarding de usuarios beta

✅ **SISTEMA LISTO PARA BETA TESTING**

**URL de producción:** https://beta-cotizador.tudominio.com  
**Estado:** PRODUCTION READY - BETA  
**Usuarios beta objetivo:** 5-10 empresas  
**Duración beta:** 4-6 semanas

---

*Conservar esta lista como documentación del despliegue exitoso.*