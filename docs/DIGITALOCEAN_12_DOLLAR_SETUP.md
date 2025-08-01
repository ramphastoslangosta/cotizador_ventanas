# DigitalOcean $12/mes Setup Guide
**Sistema de Cotización de Ventanas - Optimizado para 2GB RAM**

---

## 🎯 **Configuración Optimizada $12/mes**

**Plan:** Basic Droplet $12/mes  
**Recursos:** 1 vCPU, 2GB RAM, 50GB SSD  
**Capacidad:** 5-15 usuarios beta simultáneos  
**Multi-proyecto:** Sí, espacio para 2-3 proyectos adicionales

---

## 📋 **Paso 1: Crear Droplet en DigitalOcean**

### **1.1 Registro y Configuración**
1. Ve a https://digitalocean.com
2. Regístrate (muchas veces hay $200 crédito gratis)
3. Verifica email y agrega método de pago

### **1.2 Crear Droplet**
```
Create → Droplets

✅ Choose an image:
   - Ubuntu 22.04 LTS x64

✅ Choose plan:
   - Basic: $12/mo ($0.018/hour)
   - 1 vCPU, 2 GB, 50 GB SSD

✅ Choose datacenter:
   - New York 1 (más cercano a México)

✅ Authentication:
   - SSH Key (recomendado)
   - Password (más fácil pero menos seguro)

✅ Hostname:
   - ventanas-beta-server
```

### **1.3 Configurar SSH Key (Recomendado)**
En tu Mac/Linux:
```bash
# Generar SSH key si no tienes una
ssh-keygen -t rsa -b 4096 -C "tu-email@ejemplo.com"

# Mostrar tu public key
cat ~/.ssh/id_rsa.pub
```
Copia todo el output y pégalo en DigitalOcean.

---

## 🚀 **Paso 2: Configuración Inicial del Servidor**

### **2.1 Conectar por SSH**
```bash
# Reemplaza XXX.XXX.XXX.XXX con tu IP real
ssh root@XXX.XXX.XXX.XXX
```

### **2.2 Setup Automatizado (Recomendado)**
```bash
# Ejecutar script de configuración automática
curl -fsSL https://raw.githubusercontent.com/tu-repo/main/scripts/quick-setup.sh | bash
```

### **2.3 O Setup Manual (Paso a Paso)**
```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configurar firewall
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Crear usuario para app
adduser ventanas
usermod -aG docker ventanas
usermod -aG sudo ventanas

# Configurar swap para mejor rendimiento en 2GB RAM
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## 📁 **Paso 3: Subir tu Código**

### **3.1 Cambiar al Usuario App**
```bash
su - ventanas
```

### **3.2 Clonar/Subir Código**

**Opción A: Git Clone**
```bash
git clone https://github.com/tu-usuario/tu-repo.git app
cd app
```

**Opción B: Upload Manual**
```bash
# En tu computadora local
scp -r /ruta/local/del/proyecto/* ventanas@XXX.XXX.XXX.XXX:~/app/
```

### **3.3 Configurar Variables de Entorno**
```bash
cd ~/app
cp .env.beta.template .env
nano .env
```

**Configuración optimizada para 2GB RAM:**
```bash
# === CONFIGURACIÓN PARA $12/mes PLAN ===
DATABASE_URL="postgresql://ventanas_user:TU_PASSWORD_SEGURO@postgres:5432/ventanas_beta_db"
DB_USER="ventanas_user"  
DB_PASSWORD="TU_PASSWORD_SUPER_SEGURO_123!"

# Generar SECRET_KEY único
SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"

# Dominio (cambiar después)
ALLOWED_ORIGINS="http://XXX.XXX.XXX.XXX"

# Optimizaciones para 2GB RAM
SESSION_EXPIRE_HOURS=4
RATE_LIMIT_PER_MINUTE=50
MAX_BETA_USERS=15

# Configuración de app
DEBUG=false
APP_NAME="Sistema de Cotización - Beta"
```

---

## 🌐 **Paso 4: Configurar Dominio (Opcional)**

### **4.1 Configurar DNS**
En tu proveedor de dominio:
```
Tipo: A
Nombre: beta-cotizador (o el que prefieras)
Valor: XXX.XXX.XXX.XXX (IP de tu servidor)
TTL: 300
```

### **4.2 Configurar SSL**
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado (después de configurar DNS)
sudo certbot --nginx -d beta-cotizador.tudominio.com
```

---

## 🐳 **Paso 5: Deploy Optimizado**

### **5.1 Verificar Archivos**
```bash
cd ~/app
ls -la
# Debe incluir: docker-compose.beta.yml, scripts/deploy-beta.sh, .env
```

### **5.2 Ejecutar Deploy**
```bash
# Hacer ejecutable el script
chmod +x scripts/deploy-beta.sh

# Deploy inicial
./scripts/deploy-beta.sh deploy
```

### **5.3 Verificar Deployment**
```bash
# Ver containers corriendo
docker-compose -f docker-compose.beta.yml ps

# Ver logs
docker-compose -f docker-compose.beta.yml logs --tail=20

# Test health check
curl http://localhost:8000/health
```

---

## 📊 **Paso 6: Monitoreo de Recursos**

### **6.1 Verificar Uso de RAM**
```bash
# Ver uso de memoria
free -h

# Ver uso de containers
docker stats --no-stream
```

### **6.2 Configurar Alertas**
```bash
# Script de monitoreo de recursos
tee ~/monitor-resources.sh > /dev/null <<'EOF'
#!/bin/bash
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEMORY_USAGE -gt 85 ]; then
    echo "⚠️ Memoria alta: ${MEMORY_USAGE}% - $(date)" >> ~/alerts.log
fi
EOF

chmod +x ~/monitor-resources.sh

# Ejecutar cada 5 minutos
crontab -e
# Agregar: */5 * * * * /home/ventanas/monitor-resources.sh
```

---

## 🎯 **Optimizaciones Específicas para 2GB RAM**

### **✅ Lo que se optimizó:**

**PostgreSQL (512MB máximo):**
- shared_buffers: 128MB (25% de 512MB)
- effective_cache_size: 256MB (50% de 512MB)
- maintenance_work_mem: 32MB

**FastAPI App (768MB máximo):**
- Limite de memoria: 768MB
- Workers: 1 (en lugar de múltiples)
- Timeout aumentado para operaciones

**Redis (128MB máximo):**
- maxmemory: 96MB
- LRU policy para cache eficiente
- Persistencia optimizada

### **✅ Recursos Reservados:**
```
App FastAPI:     768MB (38%)
PostgreSQL:      512MB (26%)
Redis:           128MB (6%)
Sistema Ubuntu:  400MB (20%)
Buffer/Cache:    200MB (10%)
TOTAL:          2048MB (100%)
```

---

## 🚀 **Añadir Proyectos Adicionales**

### **Proyecto 2: Landing Page Simple**
```yaml
# Agregar a docker-compose.beta.yml
landing-page:
  image: nginx:alpine
  ports: ["8001:80"]
  deploy:
    resources:
      limits: { memory: 64M, cpus: '0.1' }
```

### **Proyecto 3: API Simple**
```yaml
# Agregar a docker-compose.beta.yml  
simple-api:
  build: ./simple-api
  ports: ["8002:8000"]
  deploy:
    resources:
      limits: { memory: 256M, cpus: '0.3' }
```

### **Nginx para Multiple Dominios**
```nginx
# /etc/nginx/sites-available/multi-sites
server {
    server_name cotizador.tudominio.com;
    location / { proxy_pass http://localhost:8000; }
}

server {
    server_name landing.tudominio.com;
    location / { proxy_pass http://localhost:8001; }
}

server {
    server_name api.tudominio.com;
    location / { proxy_pass http://localhost:8002; }
}
```

---

## 📈 **Escalabilidad y Upgrade**

### **Cuándo Hacer Upgrade a $24/mes:**
- CPU constantemente >80%
- RAM constantemente >85%
- Response times >3 segundos
- Más de 20 usuarios simultáneos

### **Cómo Hacer Upgrade:**
1. En DigitalOcean dashboard: Droplet → Resize
2. Seleccionar nuevo plan
3. ~30 segundos de downtime
4. Automáticamente más recursos disponibles

### **Optimizar Antes de Upgrade:**
```bash
# Limpiar logs viejos
docker system prune -f

# Optimizar base de datos
docker-compose exec postgres vacuumdb -U ventanas_user -d ventanas_beta_db

# Limpiar cache
docker-compose exec redis redis-cli FLUSHALL
```

---

## ✅ **Checklist Final $12/mes**

### **Sistema:**
- [ ] Droplet $12/mes creado en DigitalOcean
- [ ] Ubuntu 22.04 con Docker instalado
- [ ] Usuario 'ventanas' configurado
- [ ] Swap de 1GB configurado
- [ ] Firewall habilitado (22, 80, 443)

### **Aplicación:**
- [ ] Código subido a ~/app/
- [ ] .env configurado con passwords seguros
- [ ] docker-compose.beta.yml optimizado
- [ ] Deploy ejecutado sin errores
- [ ] Health check funcionando

### **Rendimiento:**
- [ ] Uso de RAM <80% en reposo
- [ ] Todos los containers corriendo
- [ ] Response time <2 segundos
- [ ] Monitoreo configurado

### **Funcionalidad:**
- [ ] Registro de usuario funciona
- [ ] Login exitoso
- [ ] Crear cotización funciona
- [ ] PDF se genera correctamente
- [ ] SSL configurado (si usas dominio)

---

## 🎉 **¡Listo para Beta!**

Tu sistema está optimizado para el plan $12/mes de DigitalOcean:

✅ **Rendimiento:** Suficiente para 5-15 usuarios beta  
✅ **Costo-efectivo:** Solo $12/mes vs $24/mes  
✅ **Escalable:** Fácil upgrade cuando necesites  
✅ **Multi-proyecto:** Espacio para proyectos adicionales  

**URL del sistema:** `http://TU-IP:8000` o `https://tu-dominio.com`  
**Costo total mensual:** $12 USD  
**Próximo paso:** ¡Comenzar onboarding de usuarios beta!

---

*¿Problemas? Revisa los logs con: `docker-compose -f docker-compose.beta.yml logs`*