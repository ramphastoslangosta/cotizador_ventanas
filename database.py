# database.py - Configuración de SQLAlchemy para Supabase
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, Numeric, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from typing import Optional
import os
from decimal import Decimal
import uuid

# Configuración de la base de datos
from config import settings

DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== MODELOS SQLAlchemy =====

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(Text, unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

class AppMaterial(Base):
    __tablename__ = "app_materials"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=True, unique=True)  # Código estándar del producto (ej: ALU-PER-NAC3-001)
    unit = Column(Text, nullable=False)  # ML, PZA, M2, CARTUCHO, LTS, KG
    category = Column(Text, nullable=False, default="Otros")  # Perfiles, Vidrio, Herrajes, Consumibles, Otros
    cost_per_unit = Column(Numeric(precision=12, scale=4), nullable=False)
    selling_unit_length_m = Column(Numeric(precision=8, scale=2), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class AppProduct(Base):
    __tablename__ = "app_products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    window_type = Column(Text, nullable=False)  # fija, corrediza, proyectante, etc.
    aluminum_line = Column(Text, nullable=False)  # nacional_serie_3, nacional_serie_35, etc.
    min_width_cm = Column(Numeric(precision=8, scale=2), nullable=False)
    max_width_cm = Column(Numeric(precision=8, scale=2), nullable=False)
    min_height_cm = Column(Numeric(precision=8, scale=2), nullable=False)
    max_height_cm = Column(Numeric(precision=8, scale=2), nullable=False)
    bom = Column(JSONB, nullable=False, default=list)  # Lista de BOMItems como JSON
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    client_name = Column(Text, nullable=False)
    client_email = Column(Text, nullable=True)
    client_phone = Column(Text, nullable=True)
    client_address = Column(Text, nullable=True)
    total_final = Column(Numeric(precision=12, scale=2), nullable=False)
    materials_subtotal = Column(Numeric(precision=12, scale=2), nullable=False)
    labor_subtotal = Column(Numeric(precision=12, scale=2), nullable=False)
    profit_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    indirect_costs_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    tax_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    items_count = Column(Integer, nullable=False)
    quote_data = Column(JSONB, nullable=False)  # Datos completos de la cotización
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)

class Company(Base):
    __tablename__ = "companies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)  # Un usuario = una empresa
    name = Column(Text, nullable=False, default="Mi Empresa")
    address = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    website = Column(Text, nullable=True)
    rfc = Column(Text, nullable=True)
    logo_filename = Column(Text, nullable=True)  # Nombre del archivo de logo
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Color(Base):
    __tablename__ = "colors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)  # Ej: "Blanco", "Negro", "Bronze", "Natural"
    code = Column(Text, nullable=True)   # Código hex o código interno: "#FFFFFF", "BLK", etc.
    description = Column(Text, nullable=True)  # Descripción adicional
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MaterialColor(Base):
    __tablename__ = "material_colors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    material_id = Column(BigInteger, ForeignKey('app_materials.id'), nullable=False)
    color_id = Column(BigInteger, ForeignKey('colors.id'), nullable=False)
    price_per_unit = Column(Numeric(precision=10, scale=2), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Índice único para evitar duplicados
    __table_args__ = (
        Index('idx_material_color_unique', 'material_id', 'color_id', unique=True),
    )

# ===== SERVICIOS DE BASE DE DATOS =====

class DatabaseUserService:
    """Servicio para gestión de usuarios en base de datos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email, User.is_active == True).first()
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    def create_user(self, email: str, hashed_password: str, full_name: str) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def create_session(self, user_id: uuid.UUID, token: str, expires_at) -> UserSession:
        session = UserSession(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session_by_token(self, token: str) -> Optional[UserSession]:
        return self.db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True,
            UserSession.expires_at > func.now()
        ).first()
    
    def invalidate_session(self, token: str):
        session = self.get_session_by_token(token)
        if session:
            session.is_active = False
            self.db.commit()

class DatabaseMaterialService:
    """Servicio para gestión de materiales en base de datos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_materials(self):
        return self.db.query(AppMaterial).filter(AppMaterial.is_active == True).all()
    
    def get_material_by_id(self, material_id: int) -> Optional[AppMaterial]:
        return self.db.query(AppMaterial).filter(
            AppMaterial.id == material_id, 
            AppMaterial.is_active == True
        ).first()
    
    def get_material_by_code(self, code: str) -> Optional[AppMaterial]:
        """Obtener material por su código estándar"""
        return self.db.query(AppMaterial).filter(
            AppMaterial.code == code,
            AppMaterial.is_active == True
        ).first()
    
    def create_material(self, name: str, unit: str, cost_per_unit: Decimal, 
                       category: str = "Otros",
                       code: Optional[str] = None,
                       selling_unit_length_m: Optional[Decimal] = None, 
                       description: Optional[str] = None) -> AppMaterial:
        material = AppMaterial(
            name=name,
            code=code,
            unit=unit,
            category=category,
            cost_per_unit=cost_per_unit,
            selling_unit_length_m=selling_unit_length_m,
            description=description
        )
        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)
        return material
    
    def update_material(self, material_id: int, **kwargs) -> Optional[AppMaterial]:
        material = self.get_material_by_id(material_id)
        if not material:
            return None
        
        for key, value in kwargs.items():
            if hasattr(material, key):
                setattr(material, key, value)
        
        material.updated_at = func.now()
        self.db.commit()
        self.db.refresh(material)
        return material
    
    def delete_material(self, material_id: int) -> bool:
        material = self.get_material_by_id(material_id)
        if not material:
            return False
        
        material.is_active = False
        self.db.commit()
        return True

class DatabaseProductService:
    """Servicio para gestión de productos en base de datos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_products(self):
        return self.db.query(AppProduct).filter(AppProduct.is_active == True).all()
    
    def get_product_by_id(self, product_id: int) -> Optional[AppProduct]:
        return self.db.query(AppProduct).filter(
            AppProduct.id == product_id, 
            AppProduct.is_active == True
        ).first()
    
    def create_product(self, name: str, window_type: str, aluminum_line: str,
                      min_width_cm: Decimal, max_width_cm: Decimal,
                      min_height_cm: Decimal, max_height_cm: Decimal,
                      bom: list, description: Optional[str] = None) -> AppProduct:
        product = AppProduct(
            name=name,
            window_type=window_type,
            aluminum_line=aluminum_line,
            min_width_cm=min_width_cm,
            max_width_cm=max_width_cm,
            min_height_cm=min_height_cm,
            max_height_cm=max_height_cm,
            bom=bom,
            description=description
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def update_product(self, product_id: int, **kwargs) -> Optional[AppProduct]:
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        product.updated_at = func.now()
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def delete_product(self, product_id: int) -> bool:
        product = self.get_product_by_id(product_id)
        if not product:
            return False
        
        product.is_active = False
        self.db.commit()
        return True

class DatabaseQuoteService:
    """Servicio para gestión de cotizaciones en base de datos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_quotes_by_user(self, user_id: uuid.UUID, limit: int = 50):
        return self.db.query(Quote).filter(Quote.user_id == user_id).order_by(Quote.created_at.desc()).limit(limit).all()
    
    def get_quote_by_id(self, quote_id: int, user_id: uuid.UUID) -> Optional[Quote]:
        return self.db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.user_id == user_id
        ).first()
    
    def create_quote(self, user_id: uuid.UUID, client_name: str, total_final: Decimal,
                    materials_subtotal: Decimal, labor_subtotal: Decimal,
                    profit_amount: Decimal, indirect_costs_amount: Decimal,
                    tax_amount: Decimal, items_count: int, quote_data: dict,
                    client_email: Optional[str] = None, client_phone: Optional[str] = None,
                    client_address: Optional[str] = None, notes: Optional[str] = None,
                    valid_until=None) -> Quote:
        quote = Quote(
            user_id=user_id,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            client_address=client_address,
            total_final=total_final,
            materials_subtotal=materials_subtotal,
            labor_subtotal=labor_subtotal,
            profit_amount=profit_amount,
            indirect_costs_amount=indirect_costs_amount,
            tax_amount=tax_amount,
            items_count=items_count,
            quote_data=quote_data,
            notes=notes,
            valid_until=valid_until
        )
        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)
        return quote
    
    def get_quote_statistics(self, user_id: uuid.UUID):
        """Obtiene estadísticas de cotizaciones para el dashboard"""
        total_quotes = self.db.query(Quote).filter(Quote.user_id == user_id).count()
        
        # Cotizaciones de los últimos 7 días
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_quotes = self.db.query(Quote).filter(
            Quote.user_id == user_id,
            Quote.created_at >= seven_days_ago
        ).all()
        
        return {
            "total_quotes": total_quotes,
            "recent_quotes": recent_quotes,
            "recent_count": len(recent_quotes)
        }

class DatabaseColorService:
    """Servicio para gestión de colores y precios por color"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_colors(self, active_only: bool = True):
        """Obtener todos los colores"""
        query = self.db.query(Color)
        if active_only:
            query = query.filter(Color.is_active == True)
        return query.all()
    
    def get_color_by_id(self, color_id: int) -> Optional[Color]:
        """Obtener color por ID"""
        return self.db.query(Color).filter(Color.id == color_id).first()
    
    def create_color(self, color_data: dict) -> Color:
        """Crear nuevo color"""
        color = Color(**color_data)
        self.db.add(color)
        self.db.commit()
        self.db.refresh(color)
        return color
    
    def update_color(self, color_id: int, color_data: dict) -> Optional[Color]:
        """Actualizar color"""
        color = self.get_color_by_id(color_id)
        if not color:
            return None
        
        for field, value in color_data.items():
            if hasattr(color, field) and value is not None:
                setattr(color, field, value)
        
        self.db.commit()
        self.db.refresh(color)
        return color
    
    def get_material_colors(self, material_id: int, available_only: bool = True):
        """Obtener colores disponibles para un material"""
        query = self.db.query(MaterialColor, Color).join(Color).filter(
            MaterialColor.material_id == material_id
        )
        if available_only:
            query = query.filter(
                MaterialColor.is_available == True,
                Color.is_active == True
            )
        return query.all()
    
    def create_material_color(self, material_color_data: dict) -> MaterialColor:
        """Crear relación material-color"""
        material_color = MaterialColor(**material_color_data)
        self.db.add(material_color)
        self.db.commit()
        self.db.refresh(material_color)
        return material_color
    
    def update_material_color(self, material_color_id: int, update_data: dict) -> Optional[MaterialColor]:
        """Actualizar relación material-color"""
        material_color = self.db.query(MaterialColor).filter(
            MaterialColor.id == material_color_id
        ).first()
        
        if not material_color:
            return None
        
        for field, value in update_data.items():
            if hasattr(material_color, field) and value is not None:
                setattr(material_color, field, value)
        
        self.db.commit()
        self.db.refresh(material_color)
        return material_color
    
    def delete_material_color(self, material_color_id: int) -> bool:
        """Eliminar relación material-color"""
        material_color = self.db.query(MaterialColor).filter(
            MaterialColor.id == material_color_id
        ).first()
        
        if material_color:
            self.db.delete(material_color)
            self.db.commit()
            return True
        return False
    
    def get_material_color_price(self, material_id: int, color_id: int) -> Optional[Decimal]:
        """Obtener precio específico para un material y color"""
        material_color = self.db.query(MaterialColor).filter(
            MaterialColor.material_id == material_id,
            MaterialColor.color_id == color_id,
            MaterialColor.is_available == True
        ).first()
        
        return material_color.price_per_unit if material_color else None

class DatabaseCompanyService:
    """Servicio para gestión de información de empresa"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_company_by_user(self, user_id: uuid.UUID) -> Optional[Company]:
        """Obtener información de empresa del usuario"""
        return self.db.query(Company).filter(Company.user_id == user_id).first()
    
    def create_default_company(self, user_id: uuid.UUID) -> Company:
        """Crear empresa por defecto para un usuario"""
        company = Company(
            user_id=user_id,
            name="Mi Empresa",
            address="Dirección de mi empresa",
            phone="+52 999 123 4567",
            email="contacto@miempresa.com",
            website="www.miempresa.com",
            rfc="RFC123456789"
        )
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company
    
    def update_company(self, user_id: uuid.UUID, company_data: dict) -> Optional[Company]:
        """Actualizar información de empresa"""
        company = self.get_company_by_user(user_id)
        if not company:
            # Crear empresa si no existe
            company = self.create_default_company(user_id)
        
        # Actualizar campos
        for field, value in company_data.items():
            if hasattr(company, field) and value is not None:
                setattr(company, field, value)
        
        self.db.commit()
        self.db.refresh(company)
        return company
    
    def get_or_create_company(self, user_id: uuid.UUID) -> Company:
        """Obtener empresa del usuario o crear una por defecto"""
        company = self.get_company_by_user(user_id)
        if not company:
            company = self.create_default_company(user_id)
        return company