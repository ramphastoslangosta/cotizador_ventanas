# 🚀 EJECUTAR MIGRACIÓN - PASO A PASO

## ✅ **ESTADO ACTUAL**
Los scripts de migración están listos y verificados. Procederemos con la migración de forma segura.

---

## 📋 **ORDEN DE EJECUCIÓN**

### **1️⃣ PASO 1: Migración de Categorización**

**Archivo a ejecutar:** `add_material_categories.sql`

**¿Qué hace?**
- Agrega columna `category` a la tabla `app_materials`
- Categoriza automáticamente todos los materiales existentes
- Es seguro ejecutar múltiples veces (idempotente)

**Comando:**
```sql
\i add_material_categories.sql
```

**Resultado esperado:**
```
NOTICE:  Columna category agregada exitosamente
NOTICE:  ✅ Categorización completada exitosamente

 category    | cantidad |                    ejemplos                    
-------------|----------|------------------------------------------------
 Perfiles    |        4 | Perfil L. Nacional 3' Riel Sup., ...
 Herrajes    |        5 | Cerradura Multipunto, Manija Recta, ...
 Vidrio      |        3 | Vidrio Claro 6mm, Vidrio Bronce 6mm, ...
 Consumibles |        3 | Silicón Estructural Claro, ...
```

---

### **2️⃣ PASO 2: Configuración de Colores**

**Archivo a ejecutar:** `migrate_specific_materials.sql`

**¿Qué hace?**
- Crea 5 colores base (Natural, Blanco, Bronze, Champagne, Negro)
- Configura precios específicos para los 4 perfiles identificados
- Crea 16 combinaciones material-color en total

**Comando:**
```sql
\i migrate_specific_materials.sql
```

**Resultado esperado:**
```
NOTICE:  Iniciando creación de colores base...
NOTICE:  Colores disponibles: 5
NOTICE:  Verificando configuración de colores...

        material_name         | category |   color_name   | price_per_unit 
------------------------------|----------|----------------|----------------
 Perfil Batiente Nacional     | Perfiles | Blanco         |         143.05
 Perfil Batiente Nacional     | Perfiles | Bronze         |         152.32
 Perfil Batiente Nacional     | Perfiles | Champagne      |         148.34
 Perfil Batiente Nacional     | Perfiles | Natural        |         132.45
 ...

NOTICE:  🎉 MIGRACIÓN DE COLORES COMPLETADA EXITOSAMENTE!
NOTICE:  📊 Estadísticas finales:
NOTICE:     • Total de materiales: 15
NOTICE:     • Perfiles configurados: 4
NOTICE:     • Colores disponibles: 5
NOTICE:     • Combinaciones material-color: 16
NOTICE:  ✅ Sistema listo para usar con nuevas funcionalidades!
```

---

## 🔧 **INSTRUCCIONES DE EJECUCIÓN**

### **Opción A: Using psql (Command Line)**

1. **Conectar a la base de datos:**
   ```bash
   psql -h [your_host] -U [your_user] -d [your_database]
   ```

2. **Ejecutar primera migración:**
   ```sql
   \i add_material_categories.sql
   ```

3. **Verificar resultado y ejecutar segunda migración:**
   ```sql
   \i migrate_specific_materials.sql
   ```

### **Opción B: Using pgAdmin**

1. **Abrir pgAdmin y conectar a tu base de datos**

2. **Crear nueva query y copiar contenido de `add_material_categories.sql`**

3. **Ejecutar el query y verificar resultados**

4. **Crear nueva query y copiar contenido de `migrate_specific_materials.sql`**

5. **Ejecutar el segundo query**

### **Opción C: Using DBeaver o similar**

1. **Conectar a la base de datos**

2. **Abrir SQL Editor**

3. **Ejecutar archivos en orden usando "Execute SQL Script"**

---

## ⚠️ **IMPORTANTE - ANTES DE EJECUTAR**

### **Verificaciones:**
- [ ] Tienes backup de la base de datos
- [ ] Confirmas que es la base de datos correcta
- [ ] El servidor de aplicación puede estar corriendo (la migración es compatible)

### **Características de Seguridad:**
- ✅ **Los scripts son idempotentes** - Puedes ejecutarlos múltiples veces sin problemas
- ✅ **No se eliminan datos** - Solo se agregan columnas y datos nuevos
- ✅ **Compatibilidad total** - El sistema funciona antes, durante y después
- ✅ **Fallback automático** - Si algo falla, el frontend sigue funcionando

---

## 🚨 **SI ALGO SALE MAL**

### **Problema 1: Error de conexión**
```
psql: error: could not connect to server
```
**Solución:** Verificar credenciales y conectividad de base de datos

### **Problema 2: Error de permisos**
```
ERROR: permission denied for table app_materials
```
**Solución:** Usar usuario con permisos de ALTER TABLE

### **Problema 3: Tablas no existen**
```
ERROR: relation "app_materials" does not exist
```
**Solución:** Verificar que estés en la base de datos correcta

### **Para cualquier error:**
1. **El sistema sigue funcionando** - Los errores no afectan funcionalidad existente
2. **Revisar mensaje de error específico**
3. **Consultar logs del servidor de aplicación**
4. **En último caso: usar restore desde backup**

---

## 🎯 **PRÓXIMOS PASOS DESPUÉS DE LA MIGRACIÓN**

1. **Verificar que todo funciona:**
   ```bash
   python verify_migration.py
   ```

2. **Probar la nueva UI:**
   - Ir a http://localhost:8000/materials_catalog
   - Verificar filtros de categoría
   - Probar gestión de colores en perfiles

3. **Capacitar usuarios en nuevas funcionalidades**

---

## 📞 **¿LISTO PARA CONTINUAR?**

Los scripts están optimizados y seguros. **¡Puedes proceder cuando estés listo!**

**Comando de ejecución secuencial:**
```sql
-- Paso 1: Categorización
\i add_material_categories.sql

-- Paso 2: Colores (ejecutar después del paso 1)
\i migrate_specific_materials.sql
```

**¡Todo está preparado para una migración exitosa!** 🎉