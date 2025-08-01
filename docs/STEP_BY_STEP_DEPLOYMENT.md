# Guía Paso a Paso - Despliegue Beta

**Sistema de Cotización de Ventanas v5.0.0-RESILIENT**  
**Tiempo Estimado:** 4-6 horas para despliegue completo  
**Dificultad:** Intermedio

---

## 📋 Preparación Previa

### ✅ Requisitos Previos
- [ ] Conocimientos básicos de Linux/Terminal
- [ ] Cuenta en proveedor cloud (DigitalOcean, AWS, Google Cloud)
- [ ] Dominio registrado (ej: `tudominio.com`)
- [ ] Tarjeta de crédito para servicios cloud
- [ ] 4-6 horas disponibles

### 🛠️ Herramientas Necesarias
- [ ] Terminal/Command Line
- [ ] Editor de texto (VS Code, nano, vim)
- [ ] Cliente SSH (incluido en Mac/Linux)
- [ ] Navegador web

---

## 🚀 FASE 1: Configuración del Servidor (1-2 horas)

### Paso 1.1: Crear Servidor en DigitalOcean (Recomendado)

**1. Crear cuenta en DigitalOcean:**
```
https://digitalocean.com
- Registrarse con email
- Verificar cuenta
- Agregar método de pago
```

**2. Crear Droplet (servidor):**
- Clic en "Create" → "Droplets"
- **OS:** Ubuntu 22.04 LTS x64
- **Plan:** Basic - $24/mes (2 vCPUs, 4GB RAM, 80GB SSD)
- **Datacenter:** New York 1 (más cercano a México)
- **Authentication:** SSH Key (más seguro que password)
- **Hostname:** `ventanas-beta-server`

**3. Generar SSH Key (si no tienes una):**
```bash
# En tu computadora local
ssh-keygen -t rsa -b 4096 -c "tu-email@ejemplo.com"
cat ~/.ssh/id_rsa.pub
# Copiar el contenido completo y pegarlo en DigitalOcean
```

**4. Crear Droplet y esperar 1-2 minutos**

### Paso 1.2: Configuración Inicial del Servidor

**1. Conectar por SSH:**
```bash
# Reemplazar XXX.XXX.XXX.XXX con la IP de tu servidor
ssh root@XXX.XXX.XXX.XXX
```

**2. Actualizar sistema:**
```bash
apt update && apt upgrade -y
```

**3. Instalar Docker y Docker Compose:**
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker --version
docker-compose --version
```

**4. Configurar firewall básico:**
```bash
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

**5. Crear usuario para la aplicación:**
```bash
adduser ventanas
usermod -aG docker ventanas
usermod -aG sudo ventanas
```

---

## 📁 FASE 2: Preparación del Código (30-45 min)

### Paso 2.1: Clonar Repositorio

**1. Cambiar a usuario ventanas:**
```bash
su - ventanas
```

**2. Clonar tu código:**
```bash
# Opción A: Si tienes Git configurado
git clone https://github.com/tu-usuario/tu-repositorio.git app
cd app

# Opción B: Subir archivos manualmente
mkdir app
cd app
# Usar scp desde tu computadora local:
# scp -r /ruta/local/del/proyecto/* ventanas@XXX.XXX.XXX.XXX:~/app/
```

**3. Verificar archivos necesarios:**
```bash
ls -la
# Debe incluir: main.py, requirements.txt, docker-compose.beta.yml, scripts/deploy-beta.sh
```

### Paso 2.2: Configurar Variables de Entorno

**1. Copiar template de configuración:**
```bash
cp .env.beta.template .env
```

**2. Editar configuración:**
```bash
nano .env
```

**3. Configurar valores críticos:**
```bash
# REEMPLAZAR ESTOS VALORES:

# Base de datos
DATABASE_URL="postgresql://ventanas_user:TU_PASSWORD_SEGURO@postgres:5432/ventanas_beta_db"
DB_USER="ventanas_user"
DB_PASSWORD="TU_PASSWORD_SEGURO"

# Generar SECRET_KEY
SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"

# Dominio (cambiar después de configurar DNS)
ALLOWED_ORIGINS="http://XXX.XXX.XXX.XXX"  # IP temporal, cambiar por dominio después

# Email para alertas
ALERT_EMAIL="tu-email@ejemplo.com"
```

**4. Guardar archivo (Ctrl+X, Y, Enter en nano)**

---

## 🌐 FASE 3: Configuración de Dominio (30-45 min)

### Paso 3.1: Configurar DNS

**1. En tu proveedor de dominio (GoDaddy, Namecheap, etc.):**
```
Crear registro A:
- Nombre: beta-cotizador (o el subdominio que prefieras)
- Tipo: A
- Valor: XXX.XXX.XXX.XXX (IP de tu servidor)
- TTL: 300 (5 minutos)
```

**2. Esperar propagación DNS (5-30 minutos):**
```bash
# Verificar desde tu computadora local
nslookup beta-cotizador.tudominio.com
```

### Paso 3.2: Certificado SSL con Let's Encrypt

**1. Instalar Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
```

**2. Crear configuración básica de Nginx:**
```bash
sudo mkdir -p /etc/nginx/sites-available
sudo tee /etc/nginx/sites-available/ventanas-beta > /dev/null <<EOF
server {
    listen 80;
    server_name beta-cotizador.tudominio.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/ventanas-beta /etc/nginx/sites-enabled/
```

**3. Obtener certificado SSL:**
```bash
sudo certbot --nginx -d beta-cotizador.tudominio.com
```

---

## 🐳 FASE 4: Despliegue con Docker (30-45 min)

### Paso 4.1: Preparar Despliegue

**1. Volver al directorio de la app:**
```bash
cd ~/app
```

**2. Actualizar configuración con dominio:**
```bash
nano .env
# Cambiar:
ALLOWED_ORIGINS="https://beta-cotizador.tudominio.com"
COOKIE_SECURE=true
```

**3. Hacer ejecutable el script de despliegue:**
```bash
chmod +x scripts/deploy-beta.sh
```

### Paso 4.2: Ejecutar Despliegue

**1. Primera ejecución:**
```bash
./scripts/deploy-beta.sh deploy
```

**2. El script automáticamente:**
- Construye las imágenes Docker
- Crea las bases de datos
- Inicia todos los servicios
- Ejecuta health checks

**3. Verificar que todo esté funcionando:**
```bash
docker-compose -f docker-compose.beta.yml ps
```

---

## ✅ FASE 5: Verificación del Sistema (15-30 min)

### Paso 5.1: Pruebas Básicas

**1. Verificar conectividad:**
```bash
curl -I https://beta-cotizador.tudominio.com
# Debe retornar: HTTP/2 200
```

**2. Verificar health check:**
```bash
curl https://beta-cotizador.tudominio.com/health
# Debe retornar: {"status": "healthy"}
```

**3. Probar en navegador:**
- Ve a `https://beta-cotizador.tudominio.com`
- Debe cargar la página de login
- Clic en "Registrarse" debe funcionar

### Paso 5.2: Crear Usuario Administrador

**1. Registrar primer usuario:**
- Ve al sistema web
- Clic en "Registrarse"
- Completa el formulario
- Confirma que puedes hacer login

**2. Configurar datos básicos:**
- Completa perfil de empresa
- Sube logo de prueba
- Configura materiales básicos

---

## 📊 FASE 6: Monitoreo y Logs (15 min)

### Paso 6.1: Configurar Monitoreo

**1. Verificar logs:**
```bash
# Logs de la aplicación
docker-compose -f docker-compose.beta.yml logs app

# Logs de base de datos
docker-compose -f docker-compose.beta.yml logs postgres

# Seguir logs en tiempo real
docker-compose -f docker-compose.beta.yml logs -f
```

**2. Configurar script de monitoreo:**
```bash
# Crear script de monitoreo automático
tee ~/monitor-system.sh > /dev/null <<'EOF'
#!/bin/bash
while true; do
    if ! curl -sf https://beta-cotizador.tudominio.com/health > /dev/null; then
        echo "🚨 ALERTA: Sistema no responde $(date)" | mail -s "Sistema Caído" tu-email@ejemplo.com
    fi
    sleep 300  # Verificar cada 5 minutos
done
EOF

chmod +x ~/monitor-system.sh
```

**3. Ejecutar en background:**
```bash
nohup ~/monitor-system.sh &
```

---

## 👥 FASE 7: Preparación para Usuarios Beta (30 min)

### Paso 7.1: Crear Documentación de Acceso

**1. Crear archivo con datos de acceso:**
```bash
tee ~/datos-beta-users.txt > /dev/null <<EOF
=== DATOS DE ACCESO BETA ===
URL: https://beta-cotizador.tudominio.com
Soporte: tu-email@ejemplo.com
Fecha inicio: $(date)

USUARIOS BETA:
1. Empresa: [Nombre]
   Email: [email]
   Password: [generar]
   
2. Empresa: [Nombre]
   Email: [email] 
   Password: [generar]
EOF
```

### Paso 7.2: Configurar Backup Automático

**1. Crear script de backup:**
```bash
tee ~/backup-daily.sh > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/ventanas/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup de base de datos
docker-compose -f /home/ventanas/app/docker-compose.beta.yml exec -T postgres pg_dump -U ventanas_user ventanas_beta_db > $BACKUP_DIR/backup_$DATE.sql

# Comprimir
gzip $BACKUP_DIR/backup_$DATE.sql

# Limpiar backups antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completado: backup_$DATE.sql.gz"
EOF

chmod +x ~/backup-daily.sh
```

**2. Configurar cron para backup diario:**
```bash
crontab -e
# Agregar línea:
0 2 * * * /home/ventanas/backup-daily.sh
```

---

## 🎯 CHECKLIST FINAL

### ✅ Sistema Técnico
- [ ] Servidor Ubuntu 22.04 configurado
- [ ] Docker y Docker Compose instalados
- [ ] Aplicación desplegada y funcionando
- [ ] Base de datos PostgreSQL operativa
- [ ] SSL/HTTPS configurado correctamente
- [ ] Dominio apuntando al servidor
- [ ] Health checks funcionando
- [ ] Logs configurados y accesibles
- [ ] Backups automáticos configurados
- [ ] Monitoreo básico activo

### ✅ Configuración de Aplicación
- [ ] Variables de entorno configuradas
- [ ] Primer usuario administrador creado
- [ ] Configuración básica de empresa completada
- [ ] Materiales de prueba cargados
- [ ] Primera cotización de prueba creada
- [ ] PDF generado correctamente

### ✅ Preparación para Beta Users
- [ ] Manual de usuario preparado
- [ ] Datos de acceso documentados
- [ ] Canales de soporte definidos
- [ ] Proceso de onboarding definido
- [ ] Formularios de feedback preparados

---

## 🚨 Solución de Problemas Comunes

### Problema: Docker no inicia
```bash
# Verificar status
sudo systemctl status docker

# Reiniciar si es necesario
sudo systemctl restart docker
```

### Problema: No se puede conectar a la base de datos
```bash
# Verificar logs de PostgreSQL
docker-compose -f docker-compose.beta.yml logs postgres

# Recrear base de datos
docker-compose -f docker-compose.beta.yml down
docker volume rm app_postgres_data
docker-compose -f docker-compose.beta.yml up -d
```

### Problema: SSL no funciona
```bash
# Verificar certificado
sudo certbot certificates

# Renovar si es necesario
sudo certbot renew
```

### Problema: Aplicación no responde
```bash
# Verificar containers
docker-compose -f docker-compose.beta.yml ps

# Reiniciar aplicación
docker-compose -f docker-compose.beta.yml restart app

# Ver logs de la aplicación
docker-compose -f docker-compose.beta.yml logs app
```

---

## 📞 Contacto de Emergencia

Si encuentras problemas críticos durante el despliegue:

1. **Verifica logs:** `docker-compose logs app`
2. **Reinicia servicios:** `docker-compose restart`
3. **Ejecuta rollback:** `./scripts/deploy-beta.sh rollback`
4. **Contacta soporte:** [tu-email@ejemplo.com]

---

## 🎉 ¡Felicidades!

Si completaste todos los pasos, tu **Sistema de Cotización de Ventanas Beta** está listo para usuarios reales.

**Siguiente paso:** Comenzar proceso de selección y onboarding de usuarios beta según el plan de 6 semanas.

**URL del sistema:** `https://beta-cotizador.tudominio.com`  
**Estado:** ✅ **PRODUCTION READY - BETA**