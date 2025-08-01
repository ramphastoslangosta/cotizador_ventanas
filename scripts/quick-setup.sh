#!/bin/bash
# quick-setup.sh - Script de configuración rápida para servidor beta
# Sistema de Cotización de Ventanas v5.0.0-RESILIENT

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Banner de inicio
echo -e "${GREEN}"
echo "=================================================="
echo "  Sistema de Cotización de Ventanas - Quick Setup"
echo "  Versión: v5.0.0-RESILIENT"
echo "=================================================="
echo -e "${NC}"

# Verificar que estamos en Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    error "Este script está diseñado para Ubuntu. Sistema detectado: $(lsb_release -d | cut -f2)"
    exit 1
fi

log "Sistema detectado: $(lsb_release -d | cut -f2)"

# 1. Actualizar sistema
log "Actualizando sistema..."
apt update && apt upgrade -y

# 2. Instalar dependencias básicas
log "Instalando dependencias básicas..."
apt install -y curl wget git nano ufw fail2ban htop tree

# 3. Configurar firewall
log "Configurando firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 4. Instalar Docker
log "Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    success "Docker instalado correctamente"
else
    warning "Docker ya está instalado"
fi

# 5. Instalar Docker Compose
log "Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION="v2.21.0"
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    success "Docker Compose instalado correctamente"
else
    warning "Docker Compose ya está instalado"
fi

# 6. Crear usuario para la aplicación
log "Configurando usuario 'ventanas'..."
if ! id "ventanas" &>/dev/null; then
    adduser --disabled-password --gecos "" ventanas
    usermod -aG docker ventanas
    usermod -aG sudo ventanas
    
    # Crear directorio SSH para el usuario
    mkdir -p /home/ventanas/.ssh
    cp /root/.ssh/authorized_keys /home/ventanas/.ssh/ 2>/dev/null || true
    chown -R ventanas:ventanas /home/ventanas/.ssh
    chmod 700 /home/ventanas/.ssh
    chmod 600 /home/ventanas/.ssh/authorized_keys 2>/dev/null || true
    
    success "Usuario 'ventanas' creado correctamente"
else
    warning "Usuario 'ventanas' ya existe"
fi

# 7. Configurar Nginx
log "Instalando y configurando Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx

# 8. Instalar Certbot para SSL
log "Instalando Certbot para SSL..."
apt install -y certbot python3-certbot-nginx

# 9. Configurar fail2ban para seguridad
log "Configurando fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# 10. Crear directorios necesarios
log "Creando estructura de directorios..."
su - ventanas -c "
mkdir -p ~/app/{logs,backups,static/uploads,nginx}
mkdir -p ~/.ssh
"

# 11. Configurar swapfile para mejorar rendimiento
log "Configurando swapfile..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    success "Swapfile de 2GB configurado"
else
    warning "Swapfile ya existe"
fi

# 12. Optimizar configuración del sistema
log "Optimizando configuración del sistema..."
# Aumentar límites de archivos abiertos
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimizar configuración de red
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p

# 13. Configurar log rotation
log "Configurando rotación de logs..."
tee /etc/logrotate.d/ventanas-app > /dev/null <<EOF
/home/ventanas/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su ventanas ventanas
}
EOF

# 14. Instalar herramientas de monitoreo
log "Instalando herramientas de monitoreo..."
apt install -y netdata
systemctl enable netdata
systemctl start netdata

# 15. Crear script de información del sistema
log "Creando script de información del sistema..."
tee /home/ventanas/system-info.sh > /dev/null <<'EOF'
#!/bin/bash
echo "=================================="
echo "  INFORMACIÓN DEL SISTEMA"
echo "=================================="
echo "Fecha: $(date)"
echo "Uptime: $(uptime -p)"
echo "OS: $(lsb_release -d | cut -f2)"
echo "IP Pública: $(curl -s ifconfig.me)"
echo ""
echo "=== DOCKER ==="
docker --version
docker-compose --version
echo ""
echo "=== SERVICIOS ==="
systemctl is-active nginx
systemctl is-active docker
systemctl is-active fail2ban
echo ""
echo "=== RECURSOS ==="
echo "CPU: $(nproc) cores"
echo "RAM: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $2 " (" $5 " usado)"}')"
echo ""
echo "=== PUERTOS ABIERTOS ==="
ss -tuln | grep LISTEN
echo "=================================="
EOF

chmod +x /home/ventanas/system-info.sh
chown ventanas:ventanas /home/ventanas/system-info.sh

# 16. Configurar SSH más seguro
log "Configurando SSH más seguro..."
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config
systemctl reload sshd

# 17. Mostrar información final
success "¡Configuración inicial completada!"
echo ""
echo -e "${YELLOW}=== INFORMACIÓN IMPORTANTE ===${NC}"
echo "Usuario de aplicación: ventanas"
echo "Directorio de trabajo: /home/ventanas/app"
echo "IP del servidor: $(curl -s ifconfig.me)"
echo ""
echo -e "${YELLOW}=== PRÓXIMOS PASOS ===${NC}"
echo "1. Cambiar al usuario ventanas: su - ventanas"
echo "2. Clonar tu repositorio en ~/app/"
echo "3. Configurar dominio DNS"
echo "4. Ejecutar deploy-beta.sh"
echo ""
echo -e "${GREEN}Ejecuta: su - ventanas && /home/ventanas/system-info.sh${NC}"
echo ""

# Crear recordatorio para el usuario
tee /etc/motd.tail > /dev/null <<EOF

========================================
  Sistema de Cotización de Ventanas
========================================
Usuario de la app: ventanas
Directorio de trabajo: /home/ventanas/app
Información del sistema: ~/system-info.sh

Próximos pasos:
1. su - ventanas
2. Clonar repositorio en ~/app/
3. Configurar dominio
4. Ejecutar ./scripts/deploy-beta.sh
========================================

EOF

success "¡Setup completado! Cambia al usuario 'ventanas' para continuar."