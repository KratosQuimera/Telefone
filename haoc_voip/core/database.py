"""
Gerenciamento do Banco de Dados SQLite com SQLAlchemy e Thread Safety.
Configura WAL mode, foreign keys e pool thread-safe.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from haoc_voip.config import Config
from haoc_voip.core.models import Base

logger = logging.getLogger("haoc.database")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Ativa pragmas críticos do SQLite para alta performance e confiabilidade:
    - WAL (Write-Ahead Logging) para permitir leituras concorrentes sem travar escritas.
    - foreign_keys para integridade referencial.
    - busy_timeout para evitar erros de SQLite locked em concorrência.
    - synchronous=NORMAL para escrita segura sem gargalo de I/O.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=10000;")  # 10 segundos
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()
    except Exception as exc:
        logger.warning("Falha ao aplicar PRAGMAs no SQLite: %s", exc)


class Database:
    """Singleton de conexão com banco de dados SQLite."""
    
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or Config.DATABASE_URL
        # check_same_thread=False permite uso de threads do ThreadPoolExecutor
        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            echo=False,
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        self.SessionScoped = scoped_session(self.session_factory)

    def init_db(self) -> None:
        """Cria todas as tabelas se não existirem."""
        logger.info("Inicializando banco de dados em %s", self.db_url)
        Base.metadata.create_all(bind=self.engine)
        self.verify_integrity()
        try:
            from haoc_voip.core.auth import garantir_usuario_master
            garantir_usuario_master()
        except Exception as e:
            logger.warning("Não foi possível pré-cadastrar usuário master no init_db: %s", e)

    def verify_integrity(self) -> bool:
        """Executa PRAGMA integrity_check para validar sanidade do banco."""
        with self.session_scope() as session:
            result = session.execute(text("PRAGMA integrity_check;")).scalar()
            if result == "ok":
                logger.debug("Integridade do banco de dados verificada com sucesso (OK).")
                return True
            else:
                logger.error("Falha na integridade do banco: %s", result)
                return False

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager para transações seguras.
        Realiza commit automático em caso de sucesso e rollback em caso de exceção.
        """
        session: Session = self.SessionScoped()
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Erro durante transação no banco. Rollback executado: %s", exc)
            raise
        finally:
            session.close()


# Instância global do banco de dados
db = Database()


def get_db_session() -> Session:
    """Retorna uma nova sessão para o ciclo de requisição web."""
    return db.SessionScoped()
