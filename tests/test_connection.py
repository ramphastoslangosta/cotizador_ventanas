# test_connection_fixed.py - Versión corregida del script de prueba
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def test_supabase_connection():
    """Prueba la conexión a Supabase y verifica las tablas"""
    
    print("🚀 Probando conexión a Supabase...")
    print("=" * 50)
    
    # Cargar variables de entorno PRIMERO
    load_dotenv()
    
    # Verificar que existe el archivo .env
    if not os.path.exists('.env'):
        print("❌ ERROR: Archivo .env no encontrado")
        print("💡 Crea un archivo .env en la raíz del proyecto")
        return False
    
    # Obtener URL de la base de datos
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL no encontrada en .env")
        print("💡 Agrega tu URL de Supabase al archivo .env")
        return False
    
    # Ocultar contraseña en el log
    safe_url = DATABASE_URL.replace(DATABASE_URL.split(':')[2].split('@')[0], "***")
    print(f"🔗 Conectando a: {safe_url}")
    
    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)
        
        # Probar conexión básica
        print("📡 Probando conexión básica...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("✅ Conexión exitosa!")
            print(f"📊 PostgreSQL: {version.split('PostgreSQL')[1].split('on')[0].strip()}")
            
            # Verificar tablas existentes
            print("\n🔍 Verificando tablas...")
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            required_tables = ['users', 'user_sessions', 'quotes', 'app_materials', 'app_products']
            
            print(f"📋 Tablas encontradas ({len(tables)}):")
            for table in tables:
                status = "✅" if table in required_tables else "ℹ️"
                print(f"   {status} {table}")
            
            # Verificar tablas requeridas
            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                print(f"\n⚠️  Tablas faltantes: {missing_tables}")
                print("💡 Crea estas tablas en tu dashboard de Supabase")
                return False
            else:
                print("\n✅ Todas las tablas requeridas están presentes!")
            
            # Probar consultas básicas
            print("\n🧪 Probando consultas básicas...")
            
            # Contar usuarios
            result = connection.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"👥 Usuarios en BD: {user_count}")
            
            # Contar materiales
            result = connection.execute(text("SELECT COUNT(*) FROM app_materials WHERE is_active = true"))
            materials_count = result.fetchone()[0]
            print(f"🧱 Materiales activos: {materials_count}")
            
            # Contar productos
            result = connection.execute(text("SELECT COUNT(*) FROM app_products WHERE is_active = true"))
            products_count = result.fetchone()[0]
            print(f"📦 Productos activos: {products_count}")
            
            # Contar cotizaciones
            result = connection.execute(text("SELECT COUNT(*) FROM quotes"))
            quotes_count = result.fetchone()[0]
            print(f"📋 Cotizaciones: {quotes_count}")
            
            print("\n🎉 ¡Conexión y configuración perfectas!")
            print("🚀 Ya puedes ejecutar tu aplicación con: python main.py")
            return True
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
        print("\n🔧 Posibles soluciones:")
        
        error_str = str(e).lower()
        
        if "could not translate host name" in error_str:
            print("1. ✅ Verifica que tu URL de DATABASE_URL sea correcta")
            print("2. ✅ Asegúrate de tener conexión a internet")
            
        elif "password authentication failed" in error_str:
            print("1. ✅ Verifica tu contraseña en Supabase")
            print("2. ✅ Resetea la contraseña si es necesario")
            print("3. ✅ Asegúrate de no tener espacios extra en la URL")
            
        elif "ssl" in error_str:
            print("1. ✅ Añade '?sslmode=require' al final de tu DATABASE_URL")
            
        elif "timeout" in error_str:
            print("1. ✅ Verifica tu conexión a internet")
            print("2. ✅ Asegúrate de que el proyecto Supabase esté activo")
            
        else:
            print("1. ✅ Revisa tu archivo .env")
            print("2. ✅ Verifica la URL completa de Supabase")
            print("3. ✅ Comprueba que el proyecto esté activo")
        
        return False

def check_env_file():
    """Verifica la configuración del archivo .env"""
    print("📁 Verificando archivo .env...")
    
    # Cargar variables ANTES de verificarlas
    load_dotenv()
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env no existe")
        return False
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'SESSION_EXPIRE_HOURS'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables faltantes en .env: {missing_vars}")
        return False
    
    print("✅ Archivo .env configurado correctamente")
    return True

if __name__ == "__main__":
    print("🔧 VERIFICADOR DE CONFIGURACIÓN SUPABASE")
    print("=" * 50)
    
    # Verificar dependencias
    try:
        import sqlalchemy
        import dotenv
        print("✅ Dependencias instaladas correctamente")
    except ImportError as e:
        print(f"❌ Dependencias faltantes: {e}")
        print("💡 Ejecuta: pip install sqlalchemy psycopg2-binary python-dotenv")
        sys.exit(1)
    
    # Verificar archivo .env
    if not check_env_file():
        print("\n💡 Crea tu archivo .env basado en la guía de configuración")
        sys.exit(1)
    
    # Probar conexión
    if test_supabase_connection():
        print("\n✅ TODO LISTO PARA USAR! 🎉")
    else:
        print("\n❌ Hay problemas con la configuración")
        sys.exit(1)