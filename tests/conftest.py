"""
Configurações Globais e Fixtures do Pytest.
Garante isolamento dos testes com banco SQLite temporário e mocks de ping.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Configurar variáveis de teste antes de importar módulos
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db_path = temp_db.name
temp_db.close()

temp_backup_dir = tempfile.TemporaryDirectory()

os.environ["HAOC_DATABASE_URL"] = f"sqlite:///{temp_db_path}"
os.environ["HAOC_SECRET_KEY"] = "test-secret-key-12345"
os.environ["HAOC_ALERT_EMAIL_ENABLED"] = "false"

from haoc_voip.config import Config
Config.DB_PATH = Path(temp_db_path)
Config.DATABASE_URL = f"sqlite:///{temp_db_path}"
Config.BACKUP_DIR = Path(temp_backup_dir.name)

from haoc_voip.core.database import Database, db
from haoc_voip.core.models import Base, Usuario, Bloco, Setor, Ramal, PerfilUsuario
from haoc_voip.core.auth import hash_senha
from haoc_voip.core.backup import BackupManager, backup_mgr
from haoc_voip.web.app import create_app

# Reatribuir diretório de backup nos testes
backup_mgr.backup_dir = Path(temp_backup_dir.name)
backup_mgr.db_path = Path(temp_db_path)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Inicializa banco temporário e usuários padrão para testes."""
    db.init_db()
    with db.session_scope() as session:
        # Criar blocos
        b_a = Bloco(nome="BLOCO A", cor="#0284c7", ativo=True)
        b_b = Bloco(nome="BLOCO B", cor="#0284c7", ativo=True)
        session.add_all([b_a, b_b])

        # Criar setores
        s_rec = Setor(nome="Recepção Central", ativo=True)
        s_uti = Setor(nome="UTI Adulto", ativo=True)
        session.add_all([s_rec, s_uti])

        # Criar usuários de teste
        admin_user = Usuario(
            nome="Administrador Teste",
            login="admintest",
            senha_hash=hash_senha("Admin@123"),
            perfil=PerfilUsuario.ADMINISTRADOR.value,
            ativo=True,
        )
        analista_user = Usuario(
            nome="Analista Teste",
            login="analistatest",
            senha_hash=hash_senha("Analista@123"),
            perfil=PerfilUsuario.ANALISTA.value,
            ativo=True,
        )
        visu_user = Usuario(
            nome="Visualizador Teste",
            login="visutest",
            senha_hash=hash_senha("Visu@123"),
            perfil=PerfilUsuario.VISUALIZACAO.value,
            ativo=True,
        )
        session.add_all([admin_user, analista_user, visu_user])

    yield

    # Limpeza pós-testes
    temp_backup_dir.cleanup()
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture
def app():
    """Retorna instância da aplicação Flask de testes."""
    flask_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-12345",
        "WTF_CSRF_ENABLED": False,
    })
    return flask_app


@pytest.fixture
def client(app):
    """Cliente HTTP de testes do Flask."""
    return app.test_client()
