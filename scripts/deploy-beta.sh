#!/bin/bash
# deploy-beta.sh - Script de despliegue automatizado para entorno beta
# Sistema de Cotización de Ventanas v5.0.0-RESILIENT

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
APP_NAME="Sistema de Cotización - Beta"
BACKUP_DIR="/var/backups/ventanas-beta"
COMPOSE_FILE="docker-compose.beta.yml"
HEALTH_CHECK_URL="http://localhost:8000/health"
MAX_RETRIES=5
RETRY_DELAY=10

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Función para verificar requisitos
check_requirements() {
    log "Verificando requisitos del sistema..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
        exit 1
    fi
    
    # Verificar archivo .env
    if [ ! -f ".env" ]; then
        error "Archivo .env no encontrado. Copiar desde .env.beta.template"
        exit 1
    fi
    
    # Verificar permisos de escritura
    if [ ! -w "$BACKUP_DIR" ]; then
        warning "Directorio de backup no existe, creando..."
        mkdir -p "$BACKUP_DIR" || {
            error "Error al crear directorio de backup"
            exit 1
        }
    fi
    
    success "Requisitos verificados correctamente"
}

# Función para backup de base de datos
backup_database() {
    log "Creando backup de base de datos..."
    
    local backup_file="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Extraer datos de conexión del .env
    source .env
    
    if docker-compose ps | grep -q postgres; then
        docker-compose exec -T postgres pg_dump -U postgres ventanas_beta_db > "$backup_file" || {
            error "Error al crear backup de base de datos"
            return 1
        }
        
        # Comprimir backup
        gzip "$backup_file"
        
        success "Backup creado: ${backup_file}.gz"
        
        # Limpiar backups antiguos (mantener últimos 10)
        ls -t "$BACKUP_DIR"/backup_*.sql.gz | tail -n +11 | xargs -r rm
        
    else
        warning "Base de datos no está corriendo, saltando backup"
    fi
}

# Función para verificar salud del sistema
health_check() {
    log "Verificando salud del sistema..."
    
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            success "Sistema funcionando correctamente"
            return 0
        fi
        
        retries=$((retries + 1))
        warning "Intento $retries/$MAX_RETRIES fallido, esperando ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    done
    
    error "Sistema no responde después de $MAX_RETRIES intentos"
    return 1
}

# Función para despliegue
deploy() {
    log "Iniciando despliegue de $APP_NAME..."
    
    # 1. Backup
    backup_database
    
    # 2. Detener servicios actuales
    log "Deteniendo servicios..."
    docker-compose -f $COMPOSE_FILE down || warning "Servicios ya estaban detenidos"
    
    # 3. Actualizar código
    log "Actualizando código..."
    git fetch origin
    git reset --hard origin/main
    
    # 4. Build nuevas imágenes
    log "Construyendo nuevas imágenes..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    
    # 5. Iniciar servicios
    log "Iniciando servicios..."
    docker-compose -f $COMPOSE_FILE up -d
    
    # 6. Esperar inicio completo
    log "Esperando inicio de servicios..."
    sleep 30
    
    # 7. Verificar salud
    if health_check; then
        success "✅ Despliegue completado exitosamente"
        
        # Mostrar status
        log "Estado de contenedores:"
        docker-compose -f $COMPOSE_FILE ps
        
        # Mostrar logs recientes
        log "Logs recientes:"
        docker-compose -f $COMPOSE_FILE logs --tail=20
        
        return 0
    else
        error "❌ Despliegue falló - iniciando rollback"
        rollback
        return 1
    fi
}

# Función para rollback
rollback() {
    warning "Iniciando rollback..."
    
    # Detener servicios actuales
    docker-compose -f $COMPOSE_FILE down
    
    # Volver a commit anterior
    git reset --hard HEAD~1
    
    # Restaurar último backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/backup_*.sql.gz | head -n1)
    if [ -n "$latest_backup" ]; then
        log "Restaurando backup: $latest_backup"
        gunzip -c "$latest_backup" | docker-compose exec -T postgres psql -U postgres -d ventanas_beta_db
    fi
    
    # Rebuild y restart
    docker-compose -f $COMPOSE_FILE build
    docker-compose -f $COMPOSE_FILE up -d
    
    sleep 30
    
    if health_check; then
        warning "Rollback completado - sistema restaurado"
    else
        error "CRITICAL: Rollback falló - intervención manual requerida"
        exit 1
    fi
}

# Función para mostrar logs
show_logs() {
    log "Mostrando logs del sistema..."
    docker-compose -f $COMPOSE_FILE logs -f --tail=100
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponibles:"
    echo "  deploy    - Desplegar nueva versión (default)"
    echo "  rollback  - Rollback a versión anterior"
    echo "  backup    - Crear backup manual"
    echo "  health    - Verificar salud del sistema"
    echo "  logs      - Mostrar logs en tiempo real"
    echo "  status    - Mostrar estado de contenedores"
    echo "  help      - Mostrar esta ayuda"
}

# Función para mostrar estado
show_status() {
    log "Estado del sistema:"
    docker-compose -f $COMPOSE_FILE ps
    
    log "Uso de recursos:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Función principal
main() {
    local command=${1:-deploy}
    
    case $command in
        deploy)
            check_requirements
            deploy
            ;;
        rollback)
            rollback
            ;;
        backup)
            backup_database
            ;;
        health)
            health_check
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        help)
            show_help
            ;;
        *)
            error "Comando desconocido: $command"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"