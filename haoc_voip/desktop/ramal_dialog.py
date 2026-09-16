"""
Diálogo de Cadastro e Edição de Ramais VoIP em PyQt6.
Validações de IPv4, MAC Cisco e unicidade de chaves.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from haoc_voip.core.models import Ramal, Bloco, Setor, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.importer import validar_ipv4, normalizar_mac, MAC_CISCO_REGEX
from haoc_voip.core.audit import registrar_auditoria
from haoc_voip.core.backup import backup_mgr


class RamalDialog(QDialog):
    """Diálogo modal para cadastrar ou editar um ramal VoIP Cisco."""

    def __init__(self, ramal_id: int | None = None, usuario_atual=None, parent=None):
        super().__init__(parent)
        self.ramal_id = ramal_id
        self.usuario_atual = usuario_atual
        perfil_u = getattr(usuario_atual, "perfil", None) or (usuario_atual.get("perfil") if isinstance(usuario_atual, dict) else None)
        self.is_admin = perfil_u in [PerfilUsuario.ADMINISTRADOR.value, "ADMINISTRADOR", "ANALISTA"]

        titulo = "Editar Ramal VoIP" if ramal_id else "Novo Ramal VoIP Cisco"
        self.setWindowTitle(f"HAOC VoIP Monitor - {titulo}")
        self.setMinimumWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()
        self._carregar_dados()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Descrição
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Ex: 1001 - Balcão Recepção A")
        form.addRow("Descrição *:", self.txt_desc)

        # Bloco
        self.cb_bloco = QComboBox()
        form.addRow("Bloco *:", self.cb_bloco)

        # Setor
        self.cb_setor = QComboBox()
        self.cb_setor.addItem("Sem Setor", "")
        form.addRow("Setor:", self.cb_setor)

        # IP
        self.txt_ip = QLineEdit()
        self.txt_ip.setPlaceholderText("Ex: 192.168.10.15")
        form.addRow("Endereço IPv4:", self.txt_ip)

        # MAC
        self.txt_mac = QLineEdit()
        self.txt_mac.setPlaceholderText("Ex: 00:1B:54:12:34:56")
        form.addRow("MAC Cisco:", self.txt_mac)

        # Modelo
        self.txt_modelo = QLineEdit("Cisco CP-7821")
        form.addRow("Modelo:", self.txt_modelo)

        # Criticidade
        self.cb_criticidade = QComboBox()
        self.cb_criticidade.addItems(["NORMAL", "ALTA", "CRITICA"])
        form.addRow("Criticidade:", self.cb_criticidade)

        # Localização Física
        self.txt_localizacao = QLineEdit()
        self.txt_localizacao.setPlaceholderText("Ex: 2º Andar Ala Sul - Sala 204")
        form.addRow("Localização:", self.txt_localizacao)

        # Observações
        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(70)
        self.txt_obs.setPlaceholderText("Anotações de porta de switch, patch panel...")
        form.addRow("Observações:", self.txt_obs)

        layout.addLayout(form)

        # Bloqueio de campos caso não seja administrador
        if self.ramal_id and not self.is_admin:
            self.txt_desc.setReadOnly(True)
            self.cb_bloco.setEnabled(False)
            self.txt_modelo.setReadOnly(True)
            self.cb_criticidade.setEnabled(False)
            self.txt_localizacao.setReadOnly(True)

        # Botões
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btnSecondary")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_salvar = QPushButton("Salvar Ramal")
        self.btn_salvar.clicked.connect(self._salvar)

        btn_box.addWidget(self.btn_cancelar)
        btn_box.addWidget(self.btn_salvar)
        layout.addLayout(btn_box)

    def _carregar_dados(self):
        with db.session_scope() as session:
            # Carregar blocos e setores disponíveis
            blocos = session.query(Bloco).filter(Bloco.ativo == True).order_by(Bloco.nome).all()
            for b in blocos:
                self.cb_bloco.addItem(b.nome, b.nome)

            setores = session.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()
            for s in setores:
                self.cb_setor.addItem(s.nome, s.nome)

            if self.ramal_id:
                ramal = session.query(Ramal).filter(Ramal.id == self.ramal_id).first()
                if ramal:
                    self.txt_desc.setText(ramal.descricao)
                    idx_b = self.cb_bloco.findText(ramal.bloco)
                    if idx_b >= 0:
                        self.cb_bloco.setCurrentIndex(idx_b)

                    if ramal.setor:
                        idx_s = self.cb_setor.findText(ramal.setor)
                        if idx_s >= 0:
                            self.cb_setor.setCurrentIndex(idx_s)

                    self.txt_ip.setText(ramal.ip or "")
                    self.txt_mac.setText(ramal.mac_cisco or "")
                    self.txt_modelo.setText(ramal.modelo or "Cisco CP-7821")
                    idx_c = self.cb_criticidade.findText(ramal.criticidade)
                    if idx_c >= 0:
                        self.cb_criticidade.setCurrentIndex(idx_c)
                    self.txt_localizacao.setText(ramal.localizacao or "")
                    self.txt_obs.setPlainText(ramal.observacoes or "")

    def _salvar(self):
        desc = self.txt_desc.text().strip()
        bloco = self.cb_bloco.currentText().strip()
        ip = self.txt_ip.text().strip()
        mac = normalizar_mac(self.txt_mac.text().strip())
        modelo = self.txt_modelo.text().strip() or "Cisco CP-7821"
        setor = self.cb_setor.currentData() or None
        crit = self.cb_criticidade.currentText()
        loc = self.txt_localizacao.text().strip() or None
        obs = self.txt_obs.toPlainText().strip() or None

        if not desc:
            QMessageBox.warning(self, "Aviso", "A descrição do ramal é obrigatória.")
            return

        if not bloco:
            QMessageBox.warning(self, "Aviso", "O bloco é obrigatório.")
            return

        if ip and not validar_ipv4(ip):
            QMessageBox.critical(self, "Erro de Validação", f"O endereço IP '{ip}' não é um IPv4 válido.")
            return

        if mac and not MAC_CISCO_REGEX.match(mac):
            QMessageBox.critical(self, "Erro de Validação", f"O endereço MAC '{mac}' possui formato inválido.")
            return

        user_id = self.usuario_atual.id if self.usuario_atual else None

        with db.session_scope() as session:
            # Checar duplicidades
            if ip:
                q_ip = session.query(Ramal).filter(Ramal.ip == ip, Ramal.ativo == True)
                if self.ramal_id:
                    q_ip = q_ip.filter(Ramal.id != self.ramal_id)
                dup = q_ip.first()
                if dup:
                    QMessageBox.warning(self, "Conflito de IP", f"O IP {ip} já pertence ao ramal '{dup.descricao}'.")
                    return

            # Backup preventivo
            backup_mgr.criar_backup(motivo="pre_salvar_ramal_desktop", usuario_id=user_id)

            if self.ramal_id:
                ramal = session.query(Ramal).filter(Ramal.id == self.ramal_id).first()
                if not ramal:
                    QMessageBox.critical(self, "Erro", "Ramal não encontrado.")
                    return
                ramal.ip = ip or None
                ramal.mac_cisco = mac or None
                ramal.observacoes = obs
                if self.is_admin:
                    ramal.descricao = desc
                    ramal.bloco = bloco
                    ramal.setor = setor
                    ramal.modelo = modelo
                    ramal.criticidade = crit
                    ramal.localizacao = loc

                acao = "EDITAR_RAMAL_DESKTOP"
            else:
                ramal = Ramal(
                    descricao=desc,
                    bloco=bloco,
                    setor=setor,
                    ip=ip or None,
                    mac_cisco=mac or None,
                    modelo=modelo,
                    criticidade=crit,
                    localizacao=loc,
                    observacoes=obs,
                    ativo=True,
                )
                session.add(ramal)
                session.flush()
                self.ramal_id = ramal.id
                acao = "CRIAR_RAMAL_DESKTOP"

        registrar_auditoria(
            acao=acao,
            entidade="ramal",
            entidade_id=self.ramal_id,
            detalhes={"descricao": desc, "ip": ip, "mac": mac, "bloco": bloco},
            usuario_id=user_id,
            ip_origem="desktop_client",
        )

        QMessageBox.information(self, "Sucesso", "Ramal salvo com sucesso!")
        self.accept()
