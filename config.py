# config.py - Configuración centralizada del proyecto
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/dbname"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    session_expire_hours: int = 2
    
    # Application
    app_name: str = "Sistema de Cotización de Ventanas"
    debug: bool = False
    
    # Business defaults
    default_profit_margin: float = 0.25
    default_indirect_costs: float = 0.15
    default_tax_rate: float = 0.16
    
    # Supabase (si se usa)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()