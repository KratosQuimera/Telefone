"""
Ponto de Entrada da Aplicação Desktop PyQt6.
HAOC VoIP Monitor Enterprise.
"""
import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from haoc_voip.core.database import db
from haoc_voip.desktop.login_dialog import LoginDialog
from haoc_voip.desktop.main_window import MainWindow
from haoc_voip.desktop.styles import aplicar_tema_aplicacao


def main():
    # Inicializar banco se necessário
    db.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("HAOC VoIP Monitor Enterprise")
    app.setOrganizationName("Hospital Augusto de Oliveira Camargo")

    # Aplica o tema visual institucional light com isolamento contra o modo escuro do sistema
    aplicar_tema_aplicacao(app)

    # Inicialização direta no modo livre de monitoramento (NOC de Sala)
    # Autenticação solicitada apenas ao acessar áreas sensíveis (cadastro, edição, exclusão, importação)
    janela = MainWindow(usuario_atual=None)
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
