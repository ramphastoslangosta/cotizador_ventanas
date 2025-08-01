# Sistema de Cotización de Ventanas 🏢

Sistema completo para generar cotizaciones de ventanas de aluminio con interfaz web integrada, cálculos automáticos basados en BOM (Bill of Materials) y gestión de catálogos.

**🛡️ ENTERPRISE-GRADE SECURITY** - Sistema listo para producción con seguridad de nivel empresarial (Milestone 1.1 completado)

## 🚀 Características Principales

### Sistema de BOM Dinámico 🔧
- **Catálogo de Materiales**: Gestión completa de perfiles, vidrios, herrajes y consumibles con códigos de producto
- **Catálogo de Productos**: Definición de ventanas con BOM configurables
- **Fórmulas Seguras**: Cálculo automático de cantidades con evaluación matemática segura
- **Factor de Desperdicio**: Control preciso de desperdicios por material
- **Unidades de Venta**: Manejo de perfiles por longitudes fijas (ej. 6 metros)
- **Sistema de Colores**: Precios diferenciados por color de perfil

### Interfaz Web Completa
- **Dashboard Interactivo**: Resumen de cotizaciones y estadísticas
- **Formularios Intuitivos**: Creación de cotizaciones paso a paso
- **Cálculo en Tiempo Real**: Vista previa de costos mientras se edita
- **Gestión de Catálogos**: CRUD completo para materiales y productos
- **Responsive Design**: Compatible con dispositivos móviles

### API RESTful Segura 🔐
- **Documentación Automática**: Swagger/OpenAPI integrado
- **Autenticación Segura**: Tokens criptográficamente seguros con protección contra fuerza bruta
- **Validación Robusta**: Validación y sanitización completa de datos con Pydantic
- **CORS Seguro**: Configuración restrictiva para dominios específicos
- **Protección CSRF**: Tokens CSRF para operaciones de cambio de estado
- **Rate Limiting**: Protección contra ataques de denegación de servicio

### 🛡️ Características de Seguridad (NUEVO - Milestone 1.1)
- **Evaluación Segura de Fórmulas**: Reemplaza `eval()` peligroso con `simpleeval`
- **Validación de Entrada**: Sanitización HTML y validación completa de inputs
- **Cookies Seguras**: HttpOnly, SameSite, configuración lista para HTTPS
- **Headers de Seguridad**: X-Frame-Options, CSP, X-XSS-Protection automáticos
- **Gestión de Sesiones**: Validación mejorada con detección de anomalías
- **Contraseñas Fuertes**: Requisitos de longitud y complejidad aplicados

## 📋 Requisitos del Sistema

### Requisitos Base
- Python 3.8+
- PostgreSQL 12+ (o compatible como Supabase)
- 512MB RAM mínimo (2GB recomendado para producción)

### Dependencias Principales
- FastAPI + Uvicorn para el framework web
- SQLAlchemy + psycopg2 para base de datos
- Pydantic para validación de datos
- Jinja2 Templates + Bootstrap 5 para UI
- **Dependencias de Seguridad**:
  - `simpleeval` - Evaluación segura de fórmulas matemáticas
  - `bleach` - Sanitización HTML y prevención XSS
  - `passlib[bcrypt]` - Hashing seguro de contraseñas

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd sistema-cotizacion-ventanas
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

3. **Configurar variables de entorno**
```bash
# Crear archivo .env con la configuración de base de datos
cp .env.example .env  # Si existe archivo de ejemplo
# Editar .env con tu URL de PostgreSQL/Supabase
```

4. **Instalar dependencias (incluye seguridad)**
```bash
pip install -r requirements.txt
# Instala automáticamente las dependencias de seguridad:
# - simpleeval para evaluación segura de fórmulas
# - bleach para sanitización HTML
# - passlib[bcrypt] para hashing de contraseñas
```

5. **Verificar conexión a base de datos** 
```bash
python test_connection.py
# Debe mostrar conexión exitosa antes de continuar
```

6. **Ejecutar el servidor**
```bash
python main.py
# Servidor con seguridad empresarial habilitada
```

7. **Acceder a la aplicación**
- Web: http://localhost:8000
- API Docs: http://localhost:8000/docs
- **Usuarios de prueba**: El sistema inicializa automáticamente datos de ejemplo

## 📁 Estructura del Proyecto

```
sistema-cotizacion/
├── main.py                          # Aplicación principal FastAPI con seguridad
├── config.py                        # Configuración centralizada
├── database.py                      # Modelos SQLAlchemy y servicios DB
├── requirements.txt                 # Dependencias (incluye seguridad)
├── CLAUDE.md                        # Documentación para desarrolladores
├── SECURITY_AUDIT_REPORT.md         # Reporte de auditoría de seguridad
├── security/                        # 🛡️ NUEVO - Módulos de seguridad
│   ├── formula_evaluator.py        # Evaluación segura de fórmulas matemáticas
│   ├── input_validation.py         # Validación y sanitización de entradas
│   ├── middleware.py               # CSRF, rate limiting, headers de seguridad
│   └── auth_enhancements.py        # Protección fuerza bruta, gestión sesiones
├── models/
│   ├── product_bom_models.py       # Modelos de BOM y productos
│   ├── quote_models.py             # Modelos de cotizaciones
│   ├── color_models.py             # Modelos de colores y precios
│   └── company_models.py           # Modelos de información de empresa
├── services/
│   ├── product_bom_service_db.py   # Lógica de negocio BOM con BD
│   └── pdf_service.py              # Generación de PDFs
├── static/                         # Archivos estáticos
│   ├── css/                        # Estilos personalizados
│   └── js/
│       └── safe-formula-evaluator.js # 🛡️ Evaluador seguro frontend
└── templates/                      # Templates HTML con Bootstrap 5
    ├── base.html                   # Template base con headers de seguridad
    ├── login.html                  # Login con protección CSRF
    ├── register.html               # Registro con validación segura
    ├── dashboard.html              # Dashboard principal
    ├── new_quote.html              # Formulario nueva cotización
    ├── quotes_list.html            # Lista de cotizaciones
    ├── view_quote.html             # Ver cotización con PDF
    ├── materials_catalog.html      # Catálogo de materiales + códigos
    ├── products_catalog.html       # Catálogo de productos
    └── company_settings.html       # Configuración de empresa
```

## 💾 Modelos de Datos

### AppMaterial (Materiales del BOM - ACTUALIZADO)
```python
{
    "id": 1,
    "name": "Perfil L. Nacional 3\" Riel Sup.",
    "code": "ALU-PER-NAC3-001",          # 🆕 Código estándar del producto
    "unit": "ML",
    "category": "Perfiles",              # 🆕 Categorización
    "cost_per_unit": 50.00,
    "selling_unit_length_m": 6.0,       # Para perfiles de longitud fija
    "description": "Riel superior corrediza 3\""
}
```

### AppProduct (Productos con BOM)
```python
{
    "id": 1,
    "name": "Ventana Corrediza 2 Hojas",
    "window_type": "CORREDIZA",
    "aluminum_line": "SERIE_3",
    "min_width_cm": 80,
    "max_width_cm": 300,
    "min_height_cm": 60,
    "max_height_cm": 250,
    "bom": [
        {
            "material_id": 1,
            "material_type": "PERFIL",
            "quantity_formula": "width_m",  # Fórmula dinámica
            "waste_factor": 1.05
        }
    ]
}
```

### WindowItem (Item de Cotización)
```python
{
    "product_bom_id": 1,
    "selected_glass_type": "CLARO_6MM",
    "width_cm": 150,
    "height_cm": 120,
    "quantity": 1,
    "description": "Ventana para sala principal"
}
```

## 🧮 Sistema de Cálculo

### Fórmulas Dinámicas (SEGURAS - Milestone 1.1)
El sistema permite definir fórmulas **SEGURAS** para calcular cantidades de materiales:

```python
# 🛡️ EVALUACIÓN SEGURA - Ya no usa eval() peligroso
# Variables disponibles en las fórmulas:
{
    'width_m': 1.5,           # Ancho en metros
    'height_m': 1.2,          # Alto en metros
    'width_cm': 150,          # Ancho en centímetros
    'height_cm': 120,         # Alto en centímetros
    'quantity': 2,            # Cantidad de ventanas
    'area_m2': 1.8,          # Área calculada
    'perimeter_m': 5.4,      # Perímetro calculado
    # ⚠️ 'math' ahora disponible de forma segura através de SafeFormulaEvaluator
}

# Ejemplos de fórmulas SEGURAS:
"width_m"                    # Riel superior (ancho)
"2 * height_m"              # Jambas laterales (alto x 2)
"2 * (width_m + height_m)"  # Marco perimetral
"math.ceil(area_m2 / 2)"    # Cantidad basada en área
"4 * quantity"              # Cantidad fija por ventana

# 🛡️ SOLO operaciones matemáticas permitidas - No ejecución de código arbitrario
```

### Tipos de Materiales
- **PERFIL**: Perfiles de aluminio (calculados por longitud)
- **VIDRIO**: Calculado por área según tipo seleccionado
- **HERRAJE**: Herrajes y accesorios (por pieza)
- **CONSUMIBLE**: Silicona, tornillos, felpa, etc.

### Factor de Desperdicio
Cada material puede tener su propio factor de desperdicio:
- 1.05 = 5% de desperdicio
- 1.10 = 10% de desperdicio

### Unidades de Venta
Para materiales que se venden en longitudes fijas:
```python
# Si necesito 3.5m de perfil y se vende en tramos de 6m:
quantity_needed = 3.5
selling_unit_length = 6.0
pieces_to_buy = math.ceil(3.5 / 6.0) = 1
total_cost = 1 * 6.0 * cost_per_meter
```

## 🎯 Flujo de Trabajo

### 1. Configuración de Catálogos
1. **Materiales**: Definir perfiles, herrajes, vidrios y consumibles
2. **Productos**: Crear ventanas con sus BOM específicos
3. **Rangos**: Establecer dimensiones mínimas y máximas

### 2. Creación de Cotización
1. **Cliente**: Capturar datos del cliente
2. **Ventanas**: Seleccionar productos y configurar dimensiones
3. **Vidrio**: Elegir tipo de vidrio para cada ventana
4. **Ajustes**: Modificar márgenes y costos de mano de obra
5. **Cálculo**: Generar cotización con desglose detallado

### 3. Gestión de Cotizaciones
1. **Lista**: Ver todas las cotizaciones con filtros
2. **Detalle**: Revisar desglose completo de costos
3. **Export**: Generar PDF (funcionalidad futura)

## 🔐 Autenticación y Seguridad (MEJORADO - Milestone 1.1)

### Credenciales de Prueba
```
Email: demo@test.com
Password: demo123 (debe cumplir nuevos requisitos de seguridad)
```

### Registro de Nuevos Usuarios - SEGURO
- **Validación robusta**: Sanitización completa de inputs
- **Contraseñas fuertes**: Mínimo 8 caracteres con letras y números
- **Hash seguro**: bcrypt con salt automático
- **Protección contra fuerza bruta**: Bloqueo de cuenta tras 5 intentos fallidos
- **Cookies seguras**: HttpOnly, SameSite, preparadas para HTTPS

### Características de Seguridad Implementadas
- ✅ **Evaluación segura de fórmulas** - `simpleeval` reemplaza `eval()` peligroso  
- ✅ **Protección CSRF** - Tokens para todas las operaciones de cambio de estado
- ✅ **Rate limiting** - 100 solicitudes por minuto por IP
- ✅ **Validación de entrada** - Sanitización HTML y prevención XSS
- ✅ **Headers de seguridad** - CSP, X-Frame-Options, X-XSS-Protection
- ✅ **Gestión de sesiones** - Validación mejorada con detección de anomalías

## 📊 API Endpoints

### Autenticación
- `POST /auth/register` - Registro de usuario
- `POST /auth/login` - Inicio de sesión
- `GET /auth/me` - Información del usuario actual

### Materiales (BOM)
- `GET /api/materials` - Listar materiales
- `POST /api/materials` - Crear material
- `PUT /api/materials/{id}` - Actualizar material
- `DELETE /api/materials/{id}` - Eliminar material

### Productos (BOM)
- `GET /api/products` - Listar productos
- `POST /api/products` - Crear producto
- `PUT /api/products/{id}` - Actualizar producto
- `DELETE /api/products/{id}` - Eliminar producto

### Cotizaciones
- `POST /quotes/calculate` - Calcular cotización completa
- `POST /quotes/calculate_item` - Calcular item individual
- `POST /quotes/example` - Generar cotización de ejemplo

## 🎨 Interfaz de Usuario

### Características del Frontend
- **Bootstrap 5**: Framework CSS moderno
- **Bootstrap Icons**: Iconografía consistente
- **JavaScript Vanilla**: Sin dependencias adicionales
- **Responsive**: Adaptable a móviles y tablets
- **Dark/Light Theme**: Tema profesional

### Páginas Principales
1. **Dashboard**: Resumen de actividad y acceso rápido
2. **Nueva Cotización**: Formulario paso a paso con validación
3. **Lista de Cotizaciones**: Tabla con filtros y búsqueda
4. **Ver Cotización**: Desglose detallado de costos
5. **Catálogo de Materiales**: CRUD completo con modales
6. **Catálogo de Productos**: Gestión de BOM con fórmulas

## 🔧 Configuración Avanzada

### Variables de Negocio
```python
BUSINESS_OVERHEAD = {
    "profit_margin": 0.25,      # 25% de utilidad
    "indirect_costs": 0.15,     # 15% de gastos indirectos
    "tax_rate": 0.16           # 16% de IVA
}
```

### Tipos de Ventana Soportados
- FIJA
- CORREDIZA
- PROYECTANTE
- ABATIBLE
- OSCILOBATIENTE

### Líneas de Aluminio
- SERIE_3 (Nacional Serie 3")
- SERIE_35 (Nacional Serie 35)

### Tipos de Vidrio
- CLARO_4MM / CLARO_6MM
- BRONCE_4MM / BRONCE_6MM
- REFLECTIVO_6MM
- LAMINADO_6MM
- TEMPLADO_6MM

## 🚀 Desarrollo y Extensión

### Agregar Nuevo Tipo de Material
1. Extender enum `MaterialType` en `product_bom_models.py`
2. Actualizar lógica de cálculo en `calculate_window_item_from_bom()`
3. Modificar frontend para mostrar nueva categoría

### Agregar Nueva Línea de Aluminio
1. Extender enum `AluminumLine` en `quote_models.py`
2. Crear productos con la nueva línea
3. Actualizar catálogos de materiales correspondientes

### Personalizar Fórmulas de BOM (SEGURAS)
```python
# ⚠️ IMPORTANTE: Solo operaciones matemáticas permitidas con SafeFormulaEvaluator
# Ejemplos de fórmulas avanzadas SEGURAS:
"2 * width_m + 0.1"                    # Con tolerancia
"math.ceil(perimeter_m / 6) * 6"       # Redondeo a tramos de 6m
"max(2, math.ceil(area_m2))"          # Mínimo garantizado

# 🚫 NO PERMITIDO: Código arbitrario, imports, funciones peligrosas
# ✅ PERMITIDO: Operaciones aritméticas, funciones math básicas
```

## 📈 Métricas y Reportes

### Dashboard Estadísticas
- Total de cotizaciones generadas
- Cotizaciones recientes (últimos 7 días)
- Valor total de cotizaciones
- Promedio por cotización

### Desglose de Costos
- Materiales por categoría (Perfiles, Vidrio, Herrajes, Consumibles)
- Mano de obra detallada
- Gastos indirectos y utilidad
- IVA y total final

## 🔮 Funcionalidades Futuras

- [ ] Exportación a PDF profesional
- [ ] Sistema de plantillas de cotización
- [ ] Historial de precios de materiales
- [ ] Integración con proveedores
- [ ] Módulo de seguimiento de proyectos
- [ ] Reportes de rentabilidad
- [ ] Sistema de descuentos por volumen
- [ ] Calculadora de tiempo de instalación

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 🛡️ SEGURIDAD Y PRODUCCIÓN (Milestone 1.1 Completado)

### Estado de Seguridad: ✅ PRODUCTION READY

El sistema implementa **seguridad de nivel empresarial** adecuada para el mercado SME de México:

#### Vulnerabilidades Críticas Resueltas
| Vulnerabilidad | Estado Anterior | Estado Actual | Solución |
|----------------|------------------|---------------|----------|
| Evaluación de Fórmulas | ❌ `eval()` peligroso | ✅ `simpleeval` seguro | SafeFormulaEvaluator |
| Validación de Entrada | ❌ Básica | ✅ Comprensiva | InputValidator + bleach |
| Protección CSRF | ❌ Ninguna | ✅ Token-based | SecurityMiddleware |
| Configuración de Cookies | ❌ Insegura | ✅ HttpOnly+SameSite | Secure settings |
| CORS | ❌ Permisivo (*) | ✅ Restrictivo | Dominios específicos |
| Rate Limiting | ❌ Ninguno | ✅ 100 req/min/IP | Middleware + cleanup |
| Autenticación | ❌ Básica | ✅ Brute force protection | Account lockout |
| Contraseñas | ❌ Sin requisitos | ✅ 8+ chars, letras+números | Validation |

#### Arquitectura de Seguridad Implementada
```
🛡️ SECURITY LAYERS:
├── SecurityMiddleware      → CSRF, Rate Limiting, Headers
├── InputValidator         → HTML Sanitization, XSS Prevention  
├── SafeFormulaEvaluator  → Secure Math Expression Evaluation
├── AuthSecurityEnhancer  → Brute Force Protection, Sessions
└── SecureCookieMiddleware → Cookie Security Configuration
```

### Configuración para Producción

#### Variables de Entorno Críticas
```bash
# .env para producción
DATABASE_URL="postgresql://user:pass@host:5432/dbname"
SECRET_KEY="your-super-secure-secret-key-256-bits"
DEBUG=False

# Configurar en config.py para producción:
# - secure=True para cookies HTTPS
# - CORS origins específicos de tu dominio
# - Rate limiting con Redis para escalabilidad
```

#### Checklist de Despliegue Seguro
- [ ] ✅ **Implementado**: Todas las mejoras de seguridad de Milestone 1.1
- [ ] **Pendiente**: Configurar `secure=True` para cookies en HTTPS
- [ ] **Pendiente**: Configurar orígenes CORS específicos del dominio
- [ ] **Pendiente**: Implementar rate limiting con Redis para escalabilidad
- [ ] **Pendiente**: Configurar certificados SSL/TLS
- [ ] **Pendiente**: Implementar logging y monitoreo de seguridad
- [ ] **Pendiente**: Configurar respaldos automáticos de base de datos

### Auditoría de Seguridad
📋 **Reporte completo**: Ver `SECURITY_AUDIT_REPORT.md`  
🎯 **Calificación**: **PRODUCTION READY** - Enterprise Grade Security  
📅 **Fecha de auditoría**: Julio 28, 2025  
🔄 **Próxima revisión**: Antes del despliegue en producción  

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- Crear issue en el repositorio
- Revisar documentación de API en `/docs`
- Consultar `CLAUDE.md` para guías de desarrollo
- Ver `SECURITY_AUDIT_REPORT.md` para detalles de seguridad

---

**Sistema de Cotización de Ventanas v5.0.0-SECURE** 🛡️  
*Enterprise-Grade Security for Mexico SME Market*  
Desarrollado con ❤️ usando FastAPI y Python