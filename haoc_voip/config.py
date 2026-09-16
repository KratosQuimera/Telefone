"""
Módulo de Configuração Centralizada do HAOC VoIP Monitor Enterprise.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente de .env se existir
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"

# Garantir existência de diretórios essenciais
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    """Configuração principal da aplicação."""
    
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    BACKUP_DIR: Path = BACKUP_DIR
    
    SECRET_KEY: str = os.getenv("HAOC_SECRET_KEY", "haoc-enterprise-secret-key-hospitalar-2026")
    
    # Caminho do banco de dados SQLite
    DB_PATH: Path = DATA_DIR / "haoc_voip.db"
    DATABASE_URL: str = os.getenv("HAOC_DATABASE_URL", f"sqlite:///{DB_PATH}")
    
    # Configurações de Rede e Monitoramento
    DEFAULT_PING_TIMEOUT: float = float(os.getenv("HAOC_PING_TIMEOUT_SECONDS", "1.5"))
    DEFAULT_PING_RETRIES: int = int(os.getenv("HAOC_PING_RETRIES", "2"))
    DEFAULT_SCAN_INTERVAL: int = int(os.getenv("HAOC_MONITOR_INTERVAL_SECONDS", "60"))
    MAX_CONCURRENT_THREADS: int = int(os.getenv("HAOC_MAX_THREADS", "25"))
    
    # Alertas
    ALERT_MIN_OFFLINE_SECONDS: int = int(os.getenv("HAOC_ALERT_MIN_OFFLINE_SECONDS", "120"))
    ALERT_EMAIL_ENABLED: bool = os.getenv("HAOC_ALERT_EMAIL_ENABLED", "false").lower() == "true"
    SMTP_HOST: str = os.getenv("HAOC_SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("HAOC_SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("HAOC_SMTP_USER", "")
    SMTP_PASS: str = os.getenv("HAOC_SMTP_PASS", "")
    SMTP_FROM: str = os.getenv("HAOC_SMTP_FROM", "ti.voip@haoc.hospital.local")
    SMTP_TO: str = os.getenv("HAOC_SMTP_TO", "suporte.infra@haoc.hospital.local")
    
    # Backups e Retenção
    BACKUP_RETENTION_DAYS: int = int(os.getenv("HAOC_BACKUP_RETENTION_DAYS", "30"))
    MAX_BACKUPS_COUNT: int = int(os.getenv("HAOC_MAX_BACKUPS_COUNT", "50"))
    
    # Servidor Web
    WEB_HOST: str = os.getenv("HAOC_WEB_HOST", "0.0.0.0")
    WEB_PORT: int = int(os.getenv("HAOC_WEB_PORT", "3000"))
    DEBUG: bool = os.getenv("HAOC_DEBUG", "false").lower() == "true"
    
    # Segurança e Sessão
    SESSION_TIMEOUT_MINUTES: int = 480  # 8 horas
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
