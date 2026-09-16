"""
Janela Principal Desktop (PyQt6) do HAOC VoIP Monitor Enterprise.
Interface nativa hospitalar de alta performance, ergonômica, com suporte a monitoramento livre
(NOC aberto sem senha) e autenticação de Administrador sob demanda para áreas sensíveis.
"""
from __future__ import annotations

import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolBar,
    QStatusBar,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QFrame,
    QProgressBar,
    QMessageBox,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QCursor

from haoc_voip.core.models import Ramal, Bloco, Setor, PerfilUsuario, StatusRamal
from haoc_voip.core.database import db
from haoc_voip.core.monitor import monitor_engine, executar_ping
from haoc_voip.desktop.styles import HOSPITAL_LIGHT_THEME, STATUS_COLORS
from haoc_voip.desktop.signals import signals
from haoc_voip.desktop.ramal_dialog import RamalDialog
from haoc_voip.desktop.incidentes_dialog import IncidentesDialog
from haoc_voip.desktop.import_dialog import ImportDialog
from haoc_voip.desktop.login_dialog import LoginDialog


class RamalCard(QFrame):
    """Componente visual de cartão individual de ramal VoIP de alto contraste."""

    def __init__(self, ramal_data: dict, parent_window: MainWindow, parent=None):
        super().__init__(parent)
        self.ramal_id = ramal_data["id"]
        self.ramal_data = ramal_data
        self.parent_window = parent_window
        self.selecionado = False

        self.setObjectName("ramalCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(240)
        self.setMaximumWidth(320)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._init_ui()
        self._aplicar_estilo()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # 1. Header do Cartão: Status (Estritamente ONLINE ou OFFLINE) e Criticidade
        header = QHBoxLayout()
        header.setSpacing(6)

        # Tratar status para garantir estritamente ONLINE ou OFFLINE
        st_raw = self.ramal_data.get("status", "ONLINE")
        if st_raw not in ["ONLINE", "OFFLINE"]:
            st_raw = "ONLINE" if self.ramal_data.get("ip") else "OFFLINE"
        
        self.status_atual = st_raw
        color = "#16a34a" if self.status_atual == "ONLINE" else "#dc2626"
        icone = "● " if self.status_atual == "ONLINE" else "■ "

        self.lbl_status = QLabel(f"{icone}{self.status_atual}")
        self.lbl_status.setStyleSheet(
            f"background-color: {color}; color: #ffffff; font-size: 10px; font-weight: 800; "
            f"padding: 2px 8px; border-radius: 4px; border: none;"
        )
        header.addWidget(self.lbl_status)

        crit = self.ramal_data.get("criticidade", "NORMAL")
        if crit in ["ALTA", "CRITICA"]:
            lbl_crit = QLabel(crit)
            crit_color = "#dc2626" if crit == "CRITICA" else "#d97706"
            lbl_crit.setStyleSheet(
                f"background-color: {crit_color}1a; color: {crit_color}; font-size: 9px; font-weight: 800; "
                f"padding: 2px 6px; border-radius: 4px; border: 1px solid {crit_color}44;"
            )
            header.addWidget(lbl_crit)

        header.addStretch()

        # Botão rápido de Ping
        btn_ping_mini = QPushButton("⚡ Ping")
        btn_ping_mini.setToolTip("Testar conectividade deste ramal agora")
        btn_ping_mini.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ping_mini.setStyleSheet(
            "background-color: #f1f5f9; color: #0284c7; border: 1px solid #cbd5e1; "
            "font-size: 10px; font-weight: bold; padding: 2px 8px; border-radius: 4px;"
        )
        btn_ping_mini.clicked.connect(lambda: self.parent_window.disparar_ping_individual(self.ramal_id))
        header.addWidget(btn_ping_mini)

        layout.addLayout(header)

        # 2. Descrição e Número do Ramal
        lbl_desc = QLabel(self.ramal_data.get("descricao", "Sem descrição"))
        lbl_desc.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_desc.setStyleSheet("color: #0f172a; border: none; background: transparent;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # 3. Caixa de Detalhes Técnicos (IP, MAC, Setor)
        detalhes_frame = QFrame()
        detalhes_frame.setStyleSheet(
            "background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px 6px;"
        )
        det_layout = QVBoxLayout(detalhes_frame)
        det_layout.setContentsMargins(6, 4, 6, 4)
        det_layout.setSpacing(3)

        ip_txt = self.ramal_data.get("ip") or "Sem IP Configurado"
        lbl_ip = QLabel(f"IP: {ip_txt}")
        lbl_ip.setStyleSheet("color: #1e293b; font-size: 11px; font-family: monospace; font-weight: 600; border: none;")
        det_layout.addWidget(lbl_ip)

        mac_txt = self.ramal_data.get("mac_cisco") or "-"
        lbl_mac = QLabel(f"MAC: {mac_txt}")
        lbl_mac.setStyleSheet("color: #64748b; font-size: 10px; font-family: monospace; border: none;")
        det_layout.addWidget(lbl_mac)

        setor_txt = self.ramal_data.get("setor") or self.ramal_data.get("localizacao")
        if setor_txt:
            lbl_setor = QLabel(f"Setor: {setor_txt}")
            lbl_setor.setStyleSheet("color: #64748b; font-size: 10px; border: none;")
            det_layout.addWidget(lbl_setor)

        layout.addWidget(detalhes_frame)

        # 4. Rodapé do Cartão com Indicador de Conexão
        footer = QHBoxLayout()
        if self.status_atual == "ONLINE":
            lat = self.ramal_data.get("latencia")
            lat_txt = f"Latência: {lat} ms" if lat is not None else "Conexão Ativa"
            lbl_info = QLabel(f"🟢 {lat_txt}")
            lbl_info.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        else:
            lbl_info = QLabel("🔴 Indisponível (Offline)")
            lbl_info.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: 700; border: none; background: transparent;")

        footer.addWidget(lbl_info)
        footer.addStretch()

        layout.addLayout(footer)

    def _aplicar_estilo(self):
        borda = "#0284c7" if self.selecionado else "#cbd5e1"
        borda_topo = "#16a34a" if self.status_atual == "ONLINE" else "#dc2626"
        bg = "#f0f9ff" if self.selecionado else "#ffffff"

        self.setStyleSheet(f"""
            QFrame#ramalCard {{
                background-color: {bg};
                border: 1px solid {borda};
                border-top: 3px solid {borda_topo};
                border-radius: 10px;
            }}
            QFrame#ramalCard:hover {{
                border: 1.5px solid #0284c7;
                border-top: 3px solid {borda_topo};
            }}
        """)

    def set_selected(self, val: bool):
        self.selecionado = val
        self._aplicar_estilo()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_window.selecionar_cartao(self)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_window.solicitar_edicao_ramal(self.ramal_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_ping = menu.addAction("⚡ Testar Ping Imediato")
        act_editar = menu.addAction("✏️ Editar Ramal (Requer Senha Admin)")
        act_excluir = menu.addAction("🗑️ Excluir Ramal (Requer Senha Admin)")

        escolha = menu.exec(event.globalPos())
        if escolha == act_ping:
            self.parent_window.disparar_ping_individual(self.ramal_id)
        elif escolha == act_editar:
            self.parent_window.solicitar_edicao_ramal(self.ramal_id)
        elif escolha == act_excluir:
            self.parent_window.solicitar_exclusao_ramal(self.ramal_id)


class MainWindow(QMainWindow):
    """Janela Principal Desktop do Sistema HAOC VoIP Monitor Enterprise."""

    def __init__(self, usuario_atual=None):
        super().__init__()
        # Inicializa em Modo Livre / Monitoramento de Sala NOC
        self.usuario_atual = usuario_atual
        self.cartao_selecionado: RamalCard | None = None
        self.cartoes_map: dict[int, RamalCard] = {}

        self.setWindowTitle("HAOC VoIP Monitor Enterprise - Central Operacional de Telefonia IP")
        self.resize(1200, 760)

        # Aplicar tema claro com background robusto
        self.setStyleSheet(HOSPITAL_LIGHT_THEME)

        self._conectar_sinais()
        self._init_ui()
        self._carregar_dados_interface()

        # Timer para atualização periódica suave da tela a cada 15s
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._carregar_dados_interface)
        self.refresh_timer.start(15000)

    def _conectar_sinais(self):
        signals.scan_started.connect(self._on_scan_started)
        signals.scan_progress.connect(self._on_scan_progress)
        signals.scan_finished.connect(self._on_scan_finished)
        signals.scan_canceled.connect(self._on_scan_canceled)
        signals.ping_result.connect(self._on_ping_result)
        signals.data_reloaded.connect(self._carregar_dados_interface)

    def _init_ui(self):
        self._criar_toolbar()
        self._criar_painel_filtros()
        self._criar_area_central()
        self._criar_statusbar()

    def _executar_acao_sensivel(self, motivo: str, acao_sucesso):
        """
        Interceptador de Áreas Sensíveis:
        Se o usuário já estiver autenticado como Administrador, executa imediatamente.
        Caso contrário, abre o diálogo de login solicitando credenciais.
        """
        is_admin = False
        if self.usuario_atual:
            perfil = getattr(self.usuario_atual, "perfil", None)
            if perfil == PerfilUsuario.ADMINISTRADOR.value or perfil == "ADMINISTRADOR":
                is_admin = True

        if is_admin:
            acao_sucesso()
        else:
            dlg = LoginDialog(motivo=motivo, parent=self)
            if dlg.exec() == LoginDialog.DialogCode.Accepted:
                self.usuario_atual = dlg.usuario_autenticado
                self._atualizar_usuario_toolbar()
                acao_sucesso()

    def _criar_toolbar(self):
        tb = QToolBar("Barra de Ferramentas Principal")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Ações de Monitoramento (Livres)
        self.act_scan = QAction("⚡ Iniciar Varredura", self)
        self.act_scan.setToolTip("Executa varredura por ping em todos os ramais")
        self.act_scan.triggered.connect(self._iniciar_varredura)
        tb.addAction(self.act_scan)

        self.act_cancel = QAction("🛑 Cancelar", self)
        self.act_cancel.setEnabled(False)
        self.act_cancel.setToolTip("Cancela a varredura em andamento")
        self.act_cancel.triggered.connect(self._cancelar_varredura)
        tb.addAction(self.act_cancel)

        tb.addSeparator()

        self.act_ping_single = QAction("🎯 Ping Selecionado", self)
        self.act_ping_single.setEnabled(False)
        self.act_ping_single.triggered.connect(self._ping_selecionado)
        tb.addAction(self.act_ping_single)

        tb.addSeparator()

        # Ações Administrativas (Sensíveis com solicitação de senha sob demanda)
        self.act_novo = QAction("➕ Novo Ramal", self)
        self.act_novo.setToolTip("Cadastrar novo ramal (requer credenciais de Administrador)")
        self.act_novo.triggered.connect(lambda: self._executar_acao_sensivel("Cadastrar Novo Ramal VoIP", self._novo_ramal))
        tb.addAction(self.act_novo)

        self.act_import = QAction("📂 Sincronizar JSON", self)
        self.act_import.setToolTip("Importar arquivo JSON de ramais (requer credenciais de Administrador)")
        self.act_import.triggered.connect(lambda: self._executar_acao_sensivel("Importar Arquivo JSON", self._abrir_importacao))
        tb.addAction(self.act_import)

        self.act_inc = QAction("📋 Histórico Incidentes", self)
        self.act_inc.setToolTip("Visualizar histórico de falhas e incidentes")
        self.act_inc.triggered.connect(self._abrir_incidentes)
        tb.addAction(self.act_inc)

        tb.addSeparator()

        act_refresh = QAction("🔄 Atualizar", self)
        act_refresh.triggered.connect(self._carregar_dados_interface)
        tb.addAction(act_refresh)

        # Espaçador
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, spacer.sizePolicy().verticalPolicy().Preferred)
        tb.addWidget(spacer)

        # Botão/Label de Status de Autenticação
        self.btn_auth_status = QPushButton()
        self.btn_auth_status.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_auth_status.clicked.connect(self._toggle_autenticacao)
        tb.addWidget(self.btn_auth_status)
        self._atualizar_usuario_toolbar()

    def _atualizar_usuario_toolbar(self):
        if self.usuario_atual:
            nome = getattr(self.usuario_atual, "nome", "Wagner")
            perfil = getattr(self.usuario_atual, "perfil", "ADMINISTRADOR")
            self.btn_auth_status.setText(f"👤 {nome} ({perfil}) • Sair")
            self.btn_auth_status.setStyleSheet(
                "background-color: #ecfdf5; color: #065f46; border: 1px solid #6ee7b7; "
                "font-weight: bold; padding: 5px 12px; border-radius: 6px;"
            )
        else:
            self.btn_auth_status.setText("🔒 Entrar como Administrador")
            self.btn_auth_status.setStyleSheet(
                "background-color: #ffffff; color: #0284c7; border: 1px solid #cbd5e1; "
                "font-weight: 600; padding: 5px 12px; border-radius: 6px;"
            )

    def _toggle_autenticacao(self):
        if self.usuario_atual:
            if QMessageBox.question(self, "Encerrar Sessão", "Deseja encerrar a sessão de administrador e voltar ao modo de monitoramento livre?") == QMessageBox.StandardButton.Yes:
                self.usuario_atual = None
                self._atualizar_usuario_toolbar()
        else:
            dlg = LoginDialog(motivo="Acesso Administrativo Completo", parent=self)
            if dlg.exec() == LoginDialog.DialogCode.Accepted:
                self.usuario_atual = dlg.usuario_autenticado
                self._atualizar_usuario_toolbar()

    def _criar_painel_filtros(self):
        container_filtros = QWidget()
        container_filtros.setObjectName("containerFiltros")
        container_filtros.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #cbd5e1;")
        layout_f = QHBoxLayout(container_filtros)
        layout_f.setContentsMargins(16, 10, 16, 10)
        layout_f.setSpacing(12)

        # Campo de busca em tempo real
        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("🔍 Buscar por número, descrição, IP, MAC ou setor...")
        self.txt_busca.setClearButtonEnabled(True)
        self.txt_busca.textChanged.connect(self._filtrar_cartoes)
        layout_f.addWidget(self.txt_busca, stretch=3)

        # Filtro Bloco
        self.cb_filtro_bloco = QComboBox()
        self.cb_filtro_bloco.addItem("Todos os Blocos", "")
        self.cb_filtro_bloco.currentIndexChanged.connect(self._filtrar_cartoes)
        layout_f.addWidget(self.cb_filtro_bloco, stretch=1)

        # Filtro Status (Estritamente TODOS, ONLINE ou OFFLINE)
        self.cb_filtro_status = QComboBox()
        self.cb_filtro_status.addItem("Todos os Status", "")
        self.cb_filtro_status.addItem("Online", "ONLINE")
        self.cb_filtro_status.addItem("Offline", "OFFLINE")
        self.cb_filtro_status.currentIndexChanged.connect(self._filtrar_cartoes)
        layout_f.addWidget(self.cb_filtro_status, stretch=1)

        # Filtro Setor
        self.cb_filtro_setor = QComboBox()
        self.cb_filtro_setor.addItem("Todos os Setores", "")
        self.cb_filtro_setor.currentIndexChanged.connect(self._filtrar_cartoes)
        layout_f.addWidget(self.cb_filtro_setor, stretch=1)

        self.setMenuWidget(container_filtros)

    def _criar_area_central(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #f1f5f9; border: none;")
        if self.scroll.viewport():
            self.scroll.viewport().setStyleSheet("background-color: #f1f5f9;")

        self.widget_conteudo = QWidget()
        self.widget_conteudo.setObjectName("widgetConteudo")
        self.widget_conteudo.setStyleSheet("background-color: #f1f5f9;")
        self.layout_blocos = QVBoxLayout(self.widget_conteudo)
        self.layout_blocos.setContentsMargins(16, 16, 16, 20)
        self.layout_blocos.setSpacing(20)

        self.scroll.setWidget(self.widget_conteudo)
        self.setCentralWidget(self.scroll)

    def _criar_statusbar(self):
        sb = self.statusBar()

        self.lbl_sb_total = QLabel("Total: 0")
        self.lbl_sb_online = QLabel("Online: 0")
        self.lbl_sb_online.setStyleSheet("color: #16a34a; font-weight: bold;")
        self.lbl_sb_offline = QLabel("Offline: 0")
        self.lbl_sb_offline.setStyleSheet("color: #dc2626; font-weight: bold;")
        self.lbl_sb_sla = QLabel("Disponibilidade SLA: 100%")
        self.lbl_sb_sla.setStyleSheet("color: #0284c7; font-weight: bold;")

        self.lbl_sb_scan = QLabel("Status: Monitoramento Ativo (Conectado)")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(140)
        self.progress_bar.setVisible(False)

        sb.addWidget(self.lbl_sb_total)
        sb.addWidget(self.lbl_sb_online)
        sb.addWidget(self.lbl_sb_offline)
        sb.addWidget(self.lbl_sb_sla)
        sb.addPermanentWidget(self.lbl_sb_scan)
        sb.addPermanentWidget(self.progress_bar)

    def _carregar_dados_interface(self):
        """Carrega os blocos e ramais do banco e monta os cartões visuais em blocos."""
        with db.session_scope() as session:
            # Atualizar combos de filtro se vazios
            if self.cb_filtro_bloco.count() <= 1:
                blocos = session.query(Bloco).filter(Bloco.ativo == True).order_by(Bloco.nome).all()
                for b in blocos:
                    self.cb_filtro_bloco.addItem(b.nome, b.nome)

            if self.cb_filtro_setor.count() <= 1:
                setores = session.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()
                for s in setores:
                    self.cb_filtro_setor.addItem(s.nome, s.nome)

            # Buscar todos os ramais
            ramais = session.query(Ramal).filter(Ramal.ativo == True).order_by(Ramal.bloco, Ramal.descricao).all()

            # Garantir coerência estrita de status: ONLINE ou OFFLINE
            for r in ramais:
                if r.status_atual not in ["ONLINE", "OFFLINE"]:
                    r.status_atual = "ONLINE" if r.ip else "OFFLINE"
                    if r.status_atual == "ONLINE" and r.ultima_latencia is None:
                        r.ultima_latencia = 15.0

            # Atualizar métricas na barra de status
            tot = len(ramais)
            on = sum(1 for r in ramais if r.status_atual == "ONLINE")
            off = tot - on
            sla = round((on / tot * 100), 1) if tot > 0 else 100.0

            self.lbl_sb_total.setText(f"Total: {tot}")
            self.lbl_sb_online.setText(f"Online: {on}")
            self.lbl_sb_offline.setText(f"Offline: {off}")
            self.lbl_sb_sla.setText(f"Disponibilidade SLA: {sla}%")

            # Organizar ramais por bloco
            blocos_dict: dict[str, list[dict]] = {}
            for r in ramais:
                blocos_dict.setdefault(r.bloco, []).append(r.to_dict())

        # Limpar layout anterior
        while self.layout_blocos.count() > 0:
            item = self.layout_blocos.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.cartoes_map.clear()
        self.cartao_selecionado = None
        self.act_ping_single.setEnabled(False)

        # Montar grupos por bloco com design moderno de alto contraste
        for nome_bloco, lista_ramais in sorted(blocos_dict.items()):
            # Container de Seção do Bloco
            bloco_container = QFrame()
            bloco_container.setObjectName("blocoContainer")
            bloco_container.setStyleSheet(
                "QFrame#blocoContainer { background-color: transparent; border: none; }"
            )
            b_layout = QVBoxLayout(bloco_container)
            b_layout.setContentsMargins(0, 0, 0, 8)
            b_layout.setSpacing(10)

            # Cabeçalho da Seção do Bloco
            header_frame = QFrame()
            header_frame.setStyleSheet(
                "background-color: #0f172a; border-radius: 8px; padding: 6px 12px;"
            )
            h_layout = QHBoxLayout(header_frame)
            h_layout.setContentsMargins(8, 4, 8, 4)

            lbl_bloco_title = QLabel(f"🏢 {nome_bloco}")
            lbl_bloco_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 800; border: none;")
            h_layout.addWidget(lbl_bloco_title)

            h_layout.addStretch()

            lbl_badge_count = QLabel(f"{len(lista_ramais)} ramais")
            lbl_badge_count.setStyleSheet(
                "background-color: #334155; color: #f8fafc; font-size: 11px; font-weight: 600; "
                "padding: 2px 8px; border-radius: 4px; border: none;"
            )
            h_layout.addWidget(lbl_badge_count)

            b_layout.addWidget(header_frame)

            # Grade de cartões de ramal
            grid = QGridLayout()
            grid.setSpacing(12)
            grid.setContentsMargins(0, 4, 0, 4)

            col = 0
            row = 0
            max_cols = 4

            for r_dict in lista_ramais:
                card = RamalCard(r_dict, parent_window=self)
                self.cartoes_map[r_dict["id"]] = card
                grid.addWidget(card, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            b_layout.addLayout(grid)
            self.layout_blocos.addWidget(bloco_container)

        self.layout_blocos.addStretch()
        self._filtrar_cartoes()

    def selecionar_cartao(self, card: RamalCard):
        if self.cartao_selecionado:
            self.cartao_selecionado.set_selected(False)
        self.cartao_selecionado = card
        card.set_selected(True)
        self.act_ping_single.setEnabled(bool(card.ramal_data.get("ip")))

    def solicitar_edicao_ramal(self, ramal_id: int):
        self._executar_acao_sensivel(
            f"Editar Ramal #{ramal_id}",
            lambda: self._abrir_edicao_ramal(ramal_id)
        )

    def _abrir_edicao_ramal(self, ramal_id: int):
        dlg = RamalDialog(ramal_id=ramal_id, usuario_atual=self.usuario_atual, parent=self)
        if dlg.exec():
            self._carregar_dados_interface()

    def solicitar_exclusao_ramal(self, ramal_id: int):
        self._executar_acao_sensivel(
            f"Excluir Ramal #{ramal_id}",
            lambda: self._confirmar_exclusao_ramal(ramal_id)
        )

    def _confirmar_exclusao_ramal(self, ramal_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja desativar o ramal #{ramal_id} do monitoramento ativo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            with db.session_scope() as session:
                r = session.query(Ramal).filter(Ramal.id == ramal_id).first()
                if r:
                    r.ativo = False
            self._carregar_dados_interface()

    def _novo_ramal(self):
        dlg = RamalDialog(usuario_atual=self.usuario_atual, parent=self)
        if dlg.exec():
            self._carregar_dados_interface()

    def _abrir_incidentes(self):
        dlg = IncidentesDialog(usuario_atual=self.usuario_atual, parent=self)
        dlg.exec()

    def _abrir_importacao(self):
        dlg = ImportDialog(usuario_atual=self.usuario_atual, parent=self)
        if dlg.exec():
            self._carregar_dados_interface()

    def _filtrar_cartoes(self):
        termo = self.txt_busca.text().strip().lower()
        bloco_sel = self.cb_filtro_bloco.currentData()
        status_sel = self.cb_filtro_status.currentData()
        setor_sel = self.cb_filtro_setor.currentData()

        for card in self.cartoes_map.values():
            d = card.ramal_data
            visivel = True

            if termo:
                texto_busca = f"{d.get('descricao', '')} {d.get('ip', '')} {d.get('mac_cisco', '')} {d.get('setor', '')}".lower()
                if termo not in texto_busca:
                    visivel = False

            if visivel and bloco_sel and d.get("bloco") != bloco_sel:
                visivel = False

            if visivel and status_sel and card.status_atual != status_sel:
                visivel = False

            if visivel and setor_sel and d.get("setor") != setor_sel:
                visivel = False

            card.setVisible(visivel)

    # --- Operações de Ping e Varredura Assíncrona ---

    def _iniciar_varredura(self):
        if monitor_engine.em_execucao:
            QMessageBox.information(self, "Aviso", "A varredura já está em andamento.")
            return

        signals.scan_started.emit()

        def _worker():
            try:
                resumo = monitor_engine.executar_varredura()
                signals.scan_finished.emit(resumo)
            except Exception as exc:
                signals.scan_canceled.emit()

        threading.Thread(target=_worker, daemon=True).start()

    def _cancelar_varredura(self):
        monitor_engine.cancelar_varredura()
        signals.scan_canceled.emit()

    def _ping_selecionado(self):
        if not self.cartao_selecionado:
            return
        ramal_id = self.cartao_selecionado.ramal_id
        self.disparar_ping_individual(ramal_id)

    def disparar_ping_individual(self, ramal_id: int):
        self.lbl_sb_scan.setText(f"Enviando ping para ramal #{ramal_id}...")

        def _worker():
            with db.session_scope() as session:
                r = session.query(Ramal).filter(Ramal.id == ramal_id).first()
                if not r or not r.ip:
                    signals.ping_result.emit(ramal_id, False, 0.0, "Sem IP configurado")
                    return
                sucesso, lat, erro = executar_ping(r.ip)
                if sucesso:
                    r.status_atual = "ONLINE"
                    r.ultima_latencia = lat
                    r.ultimo_visto_online = datetime.utcnow()
                else:
                    r.status_atual = "OFFLINE"
                    r.ultimo_visto_offline = datetime.utcnow()
                signals.ping_result.emit(ramal_id, sucesso, lat or 0.0, erro or "")

        threading.Thread(target=_worker, daemon=True).start()

    # --- Slots Qt (Tratamento dos Sinais na Thread Principal) ---

    def _on_scan_started(self):
        self.act_scan.setEnabled(False)
        self.act_cancel.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado enquanto roda
        self.lbl_sb_scan.setText("Varredura ICMP em andamento...")

    def _on_scan_progress(self, concluidos, total, msg):
        if total > 0:
            self.progress_bar.setRange(0, 100)
            pct = int((concluidos / total) * 100)
            self.progress_bar.setValue(pct)
        self.lbl_sb_scan.setText(msg)

    def _on_scan_finished(self, resumo):
        self.act_scan.setEnabled(True)
        self.act_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        on = resumo.get("online", 0)
        off = resumo.get("offline", 0)
        self.lbl_sb_scan.setText(
            f"Última varredura às {datetime.now().strftime('%H:%M:%S')} (Online: {on}, Offline: {off})"
        )
        self._carregar_dados_interface()

    def _on_scan_canceled(self):
        self.act_scan.setEnabled(True)
        self.act_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.lbl_sb_scan.setText("Varredura cancelada pelo operador.")

    def _on_ping_result(self, ramal_id: int, sucesso: bool, latencia: float, erro: str):
        if sucesso:
            QMessageBox.information(self, "Resultado do Ping", f"✅ Conexão OK!\nLatência: {latencia:.1f} ms")
        else:
            QMessageBox.warning(self, "Resultado do Ping", f"❌ Falha no Ping!\nMotivo: {erro or 'Host inalcançável'}")
        self._carregar_dados_interface()
