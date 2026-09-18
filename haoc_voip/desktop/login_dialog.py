"""
Diálogo de Login Seguro em PyQt6 com Controle de Acesso RBAC.
Suporta autenticação sob demanda para ações sensíveis (cadastrar, editar, excluir, importar).
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt
from haoc_voip.core.auth import autenticar_usuario
from haoc_voip.core.models import Usuario


class LoginDialog(QDialog):
    """Diálogo de autenticação para áreas sensíveis ou acesso administrativo."""

    def __init__(self, motivo: str = "", parent=None):
        super().__init__(parent)
        self.motivo = motivo
        self.setWindowTitle("HAOC VoIP Monitor - Autenticação de Administrador")
        self.setFixedSize(420, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.usuario_autenticado: Usuario | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Header institucional
        title_label = QLabel("HAOC VoIP Monitor Enterprise")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #0284c7;")
        layout.addWidget(title_label)

        if self.motivo:
            banner = QFrame()
            banner.setStyleSheet("background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 6px;")
            b_layout = QVBoxLayout(banner)
            b_layout.setContentsMargins(8, 6, 8, 6)
            b_layout.setSpacing(2)
            lbl_b_title = QLabel("🔒 Ação Sensível Requer Autenticação")
            lbl_b_title.setStyleSheet("font-weight: bold; color: #991b1b; font-size: 11px;")
            lbl_b_desc = QLabel(self.motivo)
            lbl_b_desc.setStyleSheet("color: #7f1d1d; font-size: 11px;")
            b_layout.addWidget(lbl_b_title)
            b_layout.addWidget(lbl_b_desc)
            layout.addWidget(banner)
        else:
            sub_label = QLabel("Informe as credenciais do Administrador para gerenciar o sistema.")
            sub_label.setStyleSheet("color: #64748b; font-size: 11px;")
            layout.addWidget(sub_label)

        # Campo Login
        lbl_user = QLabel("Usuário de Administrador:")
        lbl_user.setStyleSheet("font-weight: 600; color: #334155;")
        self.txt_login = QLineEdit()
        self.txt_login.setText("Wagner")
        self.txt_login.setPlaceholderText("Ex: Wagner")
        layout.addWidget(lbl_user)
        layout.addWidget(self.txt_login)

        # Campo Senha
        lbl_senha = QLabel("Senha de Acesso:")
        lbl_senha.setStyleSheet("font-weight: 600; color: #334155;")
        self.txt_senha = QLineEdit()
        self.txt_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_senha.setPlaceholderText("Senha do Administrador")
        self.txt_senha.returnPressed.connect(self._tentar_login)
        layout.addWidget(lbl_senha)
        layout.addWidget(self.txt_senha)

        layout.addSpacing(6)

        # Botões
        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("btnSecondary")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_login = QPushButton("Confirmar Acesso")
        self.btn_login.setObjectName("btnPrimary")
        self.btn_login.clicked.connect(self._tentar_login)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_login)
        layout.addLayout(btn_box)

        # Focar no campo de senha
        self.txt_senha.setFocus()

    def _tentar_login(self):
        login_val = self.txt_login.text().strip()
        senha_val = self.txt_senha.text()

        if not login_val or not senha_val:
            QMessageBox.warning(self, "Aviso", "Informe o usuário e a senha.")
            return

        usuario, erro = autenticar_usuario(login_val, senha_val, ip_origem="desktop_client")
        if erro:
            QMessageBox.critical(self, "Falha de Autenticação", erro)
            return

        self.usuario_autenticado = usuario
        self.accept()
