"""
Testes de Interface Gráfica PyQt6 Desktop.
Executa em modo offscreen/headless para validação de componentes.
"""
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication
from haoc_voip.desktop.login_dialog import LoginDialog
from haoc_voip.desktop.ramal_dialog import RamalDialog
from haoc_voip.desktop.incidentes_dialog import IncidentesDialog
from haoc_voip.desktop.import_dialog import ImportDialog
from haoc_voip.desktop.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_login_dialog_instantiation(qapp):
    dlg = LoginDialog()
    assert "Acesso" in dlg.windowTitle()
    assert dlg.txt_login is not None
    assert dlg.txt_senha is not None


def test_ramal_dialog_instantiation(qapp):
    dlg = RamalDialog()
    assert "Ramal" in dlg.windowTitle()
    assert dlg.txt_desc is not None
    assert dlg.txt_ip is not None
    assert dlg.txt_mac is not None


def test_incidentes_dialog_instantiation(qapp):
    dlg = IncidentesDialog()
    assert "Incidentes" in dlg.windowTitle()
    assert dlg.tabela is not None


def test_import_dialog_instantiation(qapp):
    dlg = ImportDialog()
    assert "Importação" in dlg.windowTitle() or "Importar" in dlg.windowTitle()
    assert dlg.tabela is not None


def test_main_window_instantiation(qapp):
    user = {"id": 1, "login": "admin", "nome": "Admin", "perfil": "ADMINISTRADOR"}
    win = MainWindow(usuario_atual=user)
    assert "HAOC VoIP Monitor" in win.windowTitle()
    assert win.cartoes_map is not None
    win.close()
