"""
Janela Principal Desktop (PyQt6) do HAOC VoIP Monitor Enterprise.
Interface nativa hospitalar de alta performance, moderna e ergonômica,
com design 100% idêntico ao painel NOC Web, suporte a monitoramento livre
(acesso imediato sem senha) e autenticação de Administrador sob demanda.
"""
from __future__ import annotations

import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStatusBar,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QFrame,
    QProgressBar,
    QMessageBox,
    QMenu,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QCursor, QAction

from haoc_voip.core.models import Ramal, Bloco, Setor, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.monitor import monitor_engine, executar_ping
from haoc_voip.desktop.styles import HOSPITAL_LIGHT_THEME, STATUS_COLORS
from haoc_voip.desktop.signals import signals
from haoc_voip.desktop.ramal_dialog import RamalDialog
from haoc_voip.desktop.incidentes_dialog import IncidentesDialog
from haoc_voip.desktop.import_dialog import ImportDialog
from haoc_voip.desktop.login_dialog import LoginDialog


class RamalCard(QFrame):
    """
    Componente visual de cartão individual de ramal VoIP idêntico ao RamalCard da Web:
    - Topo: Ícone verde de telefone, número do ramal, modelo Cisco, badge de status (Online/Offline) e botão de menu ⋮
    - Meio: Descrição detalhada do ramal
    - Caixa Cinza Suave: Bloco, Setor, IP em monospace e MAC Cisco
    - Rodapé: Latência em ms com ícone de sinal e botão de Ping rápido
    """

    def __init__(self, ramal_data: dict, parent_window: MainWindow, parent=None):
        super().__init__(parent)
        self.ramal_id = ramal_data["id"]
        self.ramal_data = ramal_data
        self.parent_window = parent_window

        self.status_atual = ramal_data.get("status", "ONLINE")
        if self.status_atual not in ["ONLINE", "OFFLINE"]:
            self.status_atual = "ONLINE" if ramal_data.get("ip") else "OFFLINE"

        self.is_online = (self.status_atual == "ONLINE")
        self.setObjectName("ramalCardOnline" if self.is_online else "ramalCardOffline")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Top Header: Ícone Telefone + Número + Modelo | Status Pill + Menu
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Ícone Telefone em container arredondado
        icon_box = QLabel("📞")
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedSize(38, 38)
        if self.is_online:
            icon_box.setStyleSheet(
                "background-color: #dcfce7; color: #16a34a; font-size: 16px; "
                "border-radius: 8px; border: 1px solid #bbf7d0;"
            )
        else:
            icon_box.setStyleSheet(
                "background-color: #fee2e2; color: #dc2626; font-size: 16px; "
                "border-radius: 8px; border: 1px solid #fecaca;"
            )
        header_layout.addWidget(icon_box)

        # Coluna Número & Modelo
        info_col = QVBoxLayout()
        info_col.setSpacing(1)

        # Extrair número limpo
        desc_full = self.ramal_data.get("descricao", "")
        numero = self.ramal_data.get("numero")
        if not numero:
            # Tentar extrair do texto "Ramal XXXX" ou "XXXX - "
            import re
            m = re.search(r"(\d{4})", desc_full)
            numero = m.group(1) if m else str(self.ramal_id)

        lbl_numero = QLabel(f"Ramal {numero}")
        lbl_numero.setStyleSheet("color: #0f172a; font-size: 15px; font-weight: 800; border: none; background: transparent;")
        info_col.addWidget(lbl_numero)

        modelo = self.ramal_data.get("modelo") or "Cisco CP-7841"
        lbl_modelo = QLabel(f"⚙️ {modelo}")
        lbl_modelo.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        info_col.addWidget(lbl_modelo)

        header_layout.addLayout(info_col)
        header_layout.addStretch()

        # Status Pill
        lbl_status = QLabel("● Online" if self.is_online else "● Offline")
        if self.is_online:
            lbl_status.setStyleSheet(
                "background-color: #ecfdf5; color: #15803d; font-size: 11px; font-weight: 700; "
                "padding: 3px 8px; border-radius: 12px; border: 1px solid #bbf7d0;"
            )
        else:
            lbl_status.setStyleSheet(
                "background-color: #fef2f2; color: #b91c1c; font-size: 11px; font-weight: 700; "
                "padding: 3px 8px; border-radius: 12px; border: 1px solid #fecaca;"
            )
        header_layout.addWidget(lbl_status)

        # Botão de Menu ⋮
        btn_menu = QPushButton("⋮")
        btn_menu.setObjectName("btnCardMenu")
        btn_menu.setFixedSize(24, 24)
        btn_menu.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_menu.setToolTip("Opções do Ramal")
        btn_menu.clicked.connect(self._abrir_menu_contexto)
        header_layout.addWidget(btn_menu)

        main_layout.addLayout(header_layout)

        # 2. Descrição
        # Limpar prefixo redundante "Ramal 2001 - " se houver
        desc_limpa = desc_full
        if " - " in desc_limpa:
            desc_limpa = desc_limpa.split(" - ", 1)[1]

        lbl_desc = QLabel(desc_limpa)
        lbl_desc.setStyleSheet("color: #1e293b; font-size: 12px; font-weight: 700; border: none; background: transparent;")
        lbl_desc.setWordWrap(True)
        lbl_desc.setMinimumHeight(28)
        main_layout.addWidget(lbl_desc)

        # 3. Caixa Detalhes Técnicos (Fundo suave #f8fafc)
        box_detalhes = QFrame()
        box_detalhes.setObjectName("cardDetailBox")
        box_detalhes.setStyleSheet(
            "background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 8px; padding: 6px 8px;"
        )
        lay_det = QVBoxLayout(box_detalhes)
        lay_det.setContentsMargins(6, 6, 6, 6)
        lay_det.setSpacing(4)

        # Bloco
        row_bloco = QHBoxLayout()
        lbl_b_tag = QLabel("📍 Bloco:")
        lbl_b_tag.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; background: transparent;")
        lbl_b_val = QLabel(self.ramal_data.get("bloco", "Bloco Central"))
        lbl_b_val.setStyleSheet("color: #334155; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        row_bloco.addWidget(lbl_b_tag)
        row_bloco.addStretch()
        row_bloco.addWidget(lbl_b_val)
        lay_det.addLayout(row_bloco)

        # Setor
        row_setor = QHBoxLayout()
        lbl_s_tag = QLabel("🏷️ Setor:")
        lbl_s_tag.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; background: transparent;")
        lbl_s_val = QLabel(self.ramal_data.get("setor", "Geral"))
        lbl_s_val.setStyleSheet("color: #334155; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        row_setor.addWidget(lbl_s_tag)
        row_setor.addStretch()
        row_setor.addWidget(lbl_s_val)
        lay_det.addLayout(row_setor)

        # IP
        row_ip = QHBoxLayout()
        lbl_ip_tag = QLabel("IP:")
        lbl_ip_tag.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; background: transparent;")
        ip_txt = self.ramal_data.get("ip") or "Sem IP"
        lbl_ip_val = QLabel(ip_txt)
        lbl_ip_val.setStyleSheet(
            "color: #0f172a; font-size: 11px; font-family: monospace; font-weight: 700; "
            "background: #ffffff; padding: 1px 4px; border-radius: 4px; border: 1px solid #e2e8f0;"
        )
        row_ip.addWidget(lbl_ip_tag)
        row_ip.addStretch()
        row_ip.addWidget(lbl_ip_val)
        lay_det.addLayout(row_ip)

        # MAC Cisco
        row_mac = QHBoxLayout()
        lbl_mac_tag = QLabel("MAC Cisco:")
        lbl_mac_tag.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; background: transparent;")
        mac_txt = self.ramal_data.get("mac_cisco") or "-"
        lbl_mac_val = QLabel(mac_txt)
        lbl_mac_val.setStyleSheet("color: #64748b; font-size: 10px; font-family: monospace; border: none; background: transparent;")
        row_mac.addWidget(lbl_mac_tag)
        row_mac.addStretch()
        row_mac.addWidget(lbl_mac_val)
        lay_det.addLayout(row_mac)

        main_layout.addWidget(box_detalhes)

        # 4. Rodapé: Latência / Status Conexão | Botão Ping
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)

        if self.is_online:
            lat = self.ramal_data.get("latencia")
            lat_str = f"📶 {lat:.0f}ms" if lat is not None else "📶 10ms"
            lbl_lat = QLabel(lat_str)
            lbl_lat.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: 700; border: none; background: transparent;")
            footer_layout.addWidget(lbl_lat)
        else:
            lbl_lat = QLabel("❌ Indisponível")
            lbl_lat.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: 700; border: none; background: transparent;")
            footer_layout.addWidget(lbl_lat)

        footer_layout.addStretch()

        btn_ping = QPushButton("🔄 Ping")
        btn_ping.setObjectName("btnCardPing")
        btn_ping.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ping.clicked.connect(lambda: self.parent_window.disparar_ping_individual(self.ramal_id))
        footer_layout.addWidget(btn_ping)

        main_layout.addLayout(footer_layout)

    def _abrir_menu_contexto(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 4px; } "
            "QMenu::item { padding: 6px 16px; font-size: 12px; color: #334155; } "
            "QMenu::item:selected { background-color: #f1f5f9; color: #0f172a; border-radius: 4px; }"
        )
        act_ping = menu.addAction("⚡ Testar Ping")
        act_editar = menu.addAction("✏️ Editar Ramal")
        act_excluir = menu.addAction("🗑️ Excluir Ramal")

        escolha = menu.exec(QCursor.pos())
        if escolha == act_ping:
            self.parent_window.disparar_ping_individual(self.ramal_id)
        elif escolha == act_editar:
            self.parent_window.solicitar_edicao_ramal(self.ramal_id)
        elif escolha == act_excluir:
            self.parent_window.solicitar_exclusao_ramal(self.ramal_id)


class MainWindow(QMainWindow):
    """
    Janela Principal do HAOC VoIP Monitor Enterprise.
    Apresenta design idêntico ao painel NOC Web:
    - Navbar superior dark (#0f172a) com logotipo verde e ações rápidas
    - Hero banner escuro do Hospital com acesso ao compilador .EXE
    - 5 cards KPI em tempo real (Total, Online, Offline, SLA, Incidentes)
    - Barra de pesquisa integrada e seleção por pílulas (Pill Filters)
    - Grade uniforme de RamalCards
    """

    def __init__(self, usuario_atual=None):
        super().__init__()
        self.usuario_atual = usuario_atual
        self.cartoes_map: dict[int, RamalCard] = {}
        self.todos_os_ramais: list[dict] = []
        self.filtro_status_ativo = "TODOS"
        self.filtro_bloco_ativo = "TODOS"

        self.setWindowTitle("HAOC VoIP Monitor Enterprise - NOC Telefonia IP")
        self.resize(1260, 850)
        self.setMinimumSize(980, 680)
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
        # Widget Central
        widget_central = QWidget()
        widget_central.setObjectName("centralWidget")
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # 1. Top Navbar Escuro (#0f172a)
        layout_principal.addWidget(self._criar_top_navbar())

        # 2. Scroll Area para todo o conteúdo abaixo da Navbar
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("mainScroll")

        self.container_conteudo = QWidget()
        self.container_conteudo.setObjectName("widgetConteudo")
        self.layout_conteudo = QVBoxLayout(self.container_conteudo)
        self.layout_conteudo.setContentsMargins(24, 20, 24, 24)
        self.layout_conteudo.setSpacing(18)

        # Hero Banner
        self.layout_conteudo.addWidget(self._criar_hero_banner())

        # 5 KPI Cards
        self.layout_conteudo.addWidget(self._criar_stats_bar())

        # Card de Busca e Filtros
        self.layout_conteudo.addWidget(self._criar_filter_card())

        # Container da Grade de Ramais
        self.grid_ramais_widget = QWidget()
        self.grid_ramais = QGridLayout(self.grid_ramais_widget)
        self.grid_ramais.setContentsMargins(0, 4, 0, 16)
        self.grid_ramais.setSpacing(14)
        self.layout_conteudo.addWidget(self.grid_ramais_widget)

        self.layout_conteudo.addStretch()

        self.scroll_area.setWidget(self.container_conteudo)
        layout_principal.addWidget(self.scroll_area)

        self.setCentralWidget(widget_central)
        self._criar_statusbar()

    # =========================================================================
    # COMPONENTES VISUAIS DA TELA
    # =========================================================================

    def _criar_top_navbar(self) -> QWidget:
        navbar = QFrame()
        navbar.setObjectName("topNavbar")
        navbar.setFixedHeight(64)

        nav_layout = QHBoxLayout(navbar)
        nav_layout.setContentsMargins(24, 8, 24, 8)
        nav_layout.setSpacing(12)

        # Logo / Marca Esquerda
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)

        logo_icon = QLabel("📞")
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setFixedSize(36, 36)
        logo_icon.setStyleSheet(
            "background-color: #059669; color: #ffffff; font-size: 16px; border-radius: 8px;"
        )
        brand_layout.addWidget(logo_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)

        lbl_brand = QLabel("HAOC VoIP")
        lbl_brand.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 800; border: none;")
        title_row.addWidget(lbl_brand)

        badge_enterprise = QLabel("ENTERPRISE")
        badge_enterprise.setStyleSheet(
            "background-color: #047857; color: #ffffff; font-size: 9px; font-weight: 800; "
            "padding: 2px 6px; border-radius: 4px; border: none;"
        )
        title_row.addWidget(badge_enterprise)
        title_row.addStretch()
        title_col.addLayout(title_row)

        lbl_sub = QLabel("Hospital Augusto de Oliveira Camargo • Centro de Telefonia IP")
        lbl_sub.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500; border: none;")
        title_col.addWidget(lbl_sub)

        brand_layout.addLayout(title_col)
        nav_layout.addLayout(brand_layout)
        nav_layout.addStretch()

        # Botões da Direita
        btn_verificar = QPushButton("⚡ Verificar Todos")
        btn_verificar.setObjectName("btnNavVerify")
        btn_verificar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_verificar.clicked.connect(self._iniciar_varredura)
        nav_layout.addWidget(btn_verificar)

        btn_novo = QPushButton("+ Novo Ramal")
        btn_novo.setObjectName("btnNavDark")
        btn_novo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_novo.clicked.connect(lambda: self._executar_acao_sensivel("Cadastrar Novo Ramal VoIP", self._novo_ramal))
        nav_layout.addWidget(btn_novo)

        btn_importar = QPushButton("📂 Importar JSON")
        btn_importar.setObjectName("btnNavDark")
        btn_importar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_importar.clicked.connect(lambda: self._executar_acao_sensivel("Importar Arquivo JSON", self._abrir_importacao))
        nav_layout.addWidget(btn_importar)

        btn_incidentes = QPushButton("⚠️ Incidentes")
        btn_incidentes.setObjectName("btnNavDark")
        btn_incidentes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_incidentes.clicked.connect(self._abrir_incidentes)
        nav_layout.addWidget(btn_incidentes)

        btn_exe = QPushButton("📦 Gerar .EXE")
        btn_exe.setObjectName("btnNavExe")
        btn_exe.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_exe.clicked.connect(self._abrir_modal_exe)
        nav_layout.addWidget(btn_exe)

        # Botão de Login / Admin
        self.btn_admin = QPushButton("🔒 Admin")
        self.btn_admin.setObjectName("btnNavAdmin")
        self.btn_admin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_admin.clicked.connect(self._toggle_admin)
        nav_layout.addWidget(self.btn_admin)

        return navbar

    def _criar_hero_banner(self) -> QWidget:
        hero = QFrame()
        hero.setObjectName("heroBanner")
        hero.setFixedHeight(72)

        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(18, 10, 18, 10)
        hero_layout.setSpacing(14)

        icon_hospital = QLabel("🏥")
        icon_hospital.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_hospital.setFixedSize(40, 40)
        icon_hospital.setStyleSheet(
            "background-color: #064e3b; color: #34d399; font-size: 20px; border-radius: 10px; border: 1px solid #059669;"
        )
        hero_layout.addWidget(icon_hospital)

        col_text = QVBoxLayout()
        col_text.setSpacing(2)

        lbl_hero_title = QLabel("Hospital Augusto de Oliveira Camargo • NOC Telefonia IP")
        lbl_hero_title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 800; border: none; background: transparent;")
        col_text.addWidget(lbl_hero_title)

        lbl_hero_sub = QLabel(
            "Monitoramento ativo e transparente de ramais VoIP corporativos. Acesso livre para consulta e status em tempo real."
        )
        lbl_hero_sub.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        col_text.addWidget(lbl_hero_sub)

        hero_layout.addLayout(col_text)
        hero_layout.addStretch()

        btn_hero_exe = QPushButton("📦 Baixar / Compilar .EXE")
        btn_hero_exe.setObjectName("btnHeroExe")
        btn_hero_exe.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_hero_exe.clicked.connect(self._abrir_modal_exe)
        hero_layout.addWidget(btn_hero_exe)

        return hero

    def _criar_stats_bar(self) -> QWidget:
        container = QWidget()
        layout_kpis = QHBoxLayout(container)
        layout_kpis.setContentsMargins(0, 0, 0, 0)
        layout_kpis.setSpacing(12)

        def _card(title: str, valor_init: str, icon_symbol: str, cor_valor: str, cor_icon_bg: str, cor_icon_txt: str):
            card = QFrame()
            card.setObjectName("kpiCard")
            card.setFixedHeight(72)
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(16, 10, 16, 10)

            v_col = QVBoxLayout()
            v_col.setSpacing(1)

            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 800; border: none; background: transparent;")
            v_col.addWidget(lbl_t)

            lbl_v = QLabel(valor_init)
            lbl_v.setStyleSheet(f"color: {cor_valor}; font-size: 22px; font-weight: 900; border: none; background: transparent;")
            v_col.addWidget(lbl_v)

            c_lay.addLayout(v_col)
            c_lay.addStretch()

            lbl_ico = QLabel(icon_symbol)
            lbl_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_ico.setFixedSize(36, 36)
            lbl_ico.setStyleSheet(
                f"background-color: {cor_icon_bg}; color: {cor_icon_txt}; font-size: 16px; border-radius: 18px;"
            )
            c_lay.addWidget(lbl_ico)

            return card, lbl_v

        # 1. Total Ramais
        c1, self.lbl_kpi_total = _card("TOTAL RAMAIS", "13", "📞", "#0f172a", "#f1f5f9", "#475569")
        # 2. Online
        c2, self.lbl_kpi_online = _card("ONLINE", "13", "✓", "#16a34a", "#ecfdf5", "#16a34a")
        # 3. Offline
        c3, self.lbl_kpi_offline = _card("OFFLINE", "0", "✕", "#dc2626", "#fef2f2", "#dc2626")
        # 4. Disponibilidade SLA
        c4, self.lbl_kpi_sla = _card("DISPONIBILIDADE SLA", "100%", "📈", "#0284c7", "#f0f9ff", "#0284c7")
        # 5. Incidentes
        c5, self.lbl_kpi_inc = _card("INCIDENTES", "0", "⚠️", "#7c3aed", "#faf5ff", "#7c3aed")

        layout_kpis.addWidget(c1)
        layout_kpis.addWidget(c2)
        layout_kpis.addWidget(c3)
        layout_kpis.addWidget(c4)
        layout_kpis.addWidget(c5)

        return container

    def _criar_filter_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("filterCard")

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(12)

        # Linha 1: Input de Busca + Pills de Status (Todos, Online, Offline)
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.edit_busca = QLineEdit()
        self.edit_busca.setObjectName("searchEdit")
        self.edit_busca.setPlaceholderText("🔍 Buscar por número, descrição, setor, IPv4 ou MAC...")
        self.edit_busca.setClearButtonEnabled(True)
        self.edit_busca.textChanged.connect(self._aplicar_filtros)
        top_row.addWidget(self.edit_busca, stretch=3)

        # Container das Pills de Status
        pills_status_lay = QHBoxLayout()
        pills_status_lay.setSpacing(6)

        self.btn_status_todos = QPushButton("Todos (13)")
        self.btn_status_todos.setObjectName("pillStatusAllActive")
        self.btn_status_todos.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_status_todos.clicked.connect(lambda: self._set_filtro_status("TODOS"))
        pills_status_lay.addWidget(self.btn_status_todos)

        self.btn_status_online = QPushButton("● Online (13)")
        self.btn_status_online.setObjectName("pillStatusOnline")
        self.btn_status_online.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_status_online.clicked.connect(lambda: self._set_filtro_status("ONLINE"))
        pills_status_lay.addWidget(self.btn_status_online)

        self.btn_status_offline = QPushButton("⊗ Offline (0)")
        self.btn_status_offline.setObjectName("pillStatusOffline")
        self.btn_status_offline.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_status_offline.clicked.connect(lambda: self._set_filtro_status("OFFLINE"))
        pills_status_lay.addWidget(self.btn_status_offline)

        top_row.addLayout(pills_status_lay)
        lay.addLayout(top_row)

        # Linha Separadora
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #f1f5f9; max-height: 1px; border: none;")
        lay.addWidget(div)

        # Linha 2: Pills de Blocos Hospitalares
        self.blocos_row = QHBoxLayout()
        self.blocos_row.setSpacing(6)

        lbl_bloco_tag = QLabel("🏢 Bloco:")
        lbl_bloco_tag.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        self.blocos_row.addWidget(lbl_bloco_tag)

        self.blocos_pills_container = QHBoxLayout()
        self.blocos_pills_container.setSpacing(6)
        self.blocos_row.addLayout(self.blocos_pills_container)
        self.blocos_row.addStretch()

        lay.addLayout(self.blocos_row)

        return card

    def _criar_statusbar(self):
        sb = self.statusBar()
        sb.setFixedHeight(28)

        self.lbl_sb_msg = QLabel("Sistema operando em monitoramento contínuo • Acesso Livre NOC")
        self.lbl_sb_msg.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")
        sb.addWidget(self.lbl_sb_msg)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setVisible(False)
        sb.addPermanentWidget(self.progress_bar)

    # =========================================================================
    # LÓGICA DE DADOS, FILTROS E RENDERIZAÇÃO DE CARDS
    # =========================================================================

    def _carregar_dados_interface(self):
        """Busca ramais do SQLite e recalcula estatísticas e blocos."""
        with db.session_scope() as session:
            ramais = session.query(Ramal).filter(Ramal.ativo == True).order_by(Ramal.bloco, Ramal.descricao).all()
            self.todos_os_ramais = [r.to_dict() for r in ramais]

        # Garantir coerência estrita de status: ONLINE ou OFFLINE
        for r in self.todos_os_ramais:
            if r.get("status") not in ["ONLINE", "OFFLINE"]:
                r["status"] = "ONLINE" if r.get("ip") else "OFFLINE"

        tot = len(self.todos_os_ramais)
        on = sum(1 for r in self.todos_os_ramais if r.get("status") == "ONLINE")
        off = tot - on
        sla = round((on / tot * 100), 1) if tot > 0 else 100.0

        # Atualizar KPI Cards
        self.lbl_kpi_total.setText(str(tot))
        self.lbl_kpi_online.setText(f"{on}")
        self.lbl_kpi_offline.setText(str(off))
        self.lbl_kpi_sla.setText(f"{sla}%")
        self.lbl_kpi_inc.setText("0")

        # Atualizar labels das pills de status
        self.btn_status_todos.setText(f"Todos ({tot})")
        self.btn_status_online.setText(f"● Online ({on})")
        self.btn_status_offline.setText(f"⊗ Offline ({off})")

        self._atualizar_pills_blocos()
        self._renderizar_grade_ramais()

    def _atualizar_pills_blocos(self):
        # Limpar pills de bloco anteriores
        while self.blocos_pills_container.count() > 0:
            item = self.blocos_pills_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Extrair blocos únicos e contagens
        contagem_blocos: dict[str, int] = {}
        for r in self.todos_os_ramais:
            blk = r.get("bloco") or "Geral"
            contagem_blocos[blk] = contagem_blocos.get(blk, 0) + 1

        # Botão Todos os Blocos
        btn_todos_b = QPushButton(f"Todos os Blocos ({len(self.todos_os_ramais)})")
        if self.filtro_bloco_ativo == "TODOS":
            btn_todos_b.setObjectName("pillBlocoActive")
        else:
            btn_todos_b.setObjectName("pillBloco")
        btn_todos_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_todos_b.clicked.connect(lambda: self._set_filtro_bloco("TODOS"))
        self.blocos_pills_container.addWidget(btn_todos_b)

        for nome_bloco in sorted(contagem_blocos.keys()):
            qtd = contagem_blocos[nome_bloco]
            btn_b = QPushButton(f"{nome_bloco} ({qtd})")
            if self.filtro_bloco_ativo == nome_bloco:
                btn_b.setObjectName("pillBlocoActive")
            else:
                btn_b.setObjectName("pillBloco")
            btn_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_b.clicked.connect(lambda checked=False, b=nome_bloco: self._set_filtro_bloco(b))
            self.blocos_pills_container.addWidget(btn_b)

    def _set_filtro_status(self, novo_status: str):
        self.filtro_status_ativo = novo_status
        self.btn_status_todos.setObjectName("pillStatusAllActive" if novo_status == "TODOS" else "pillStatusAll")
        self.btn_status_online.setObjectName("pillStatusOnlineActive" if novo_status == "ONLINE" else "pillStatusOnline")
        self.btn_status_offline.setObjectName("pillStatusOfflineActive" if novo_status == "OFFLINE" else "pillStatusOffline")

        # Forçar reavaliação de estilo no Qt
        for btn in [self.btn_status_todos, self.btn_status_online, self.btn_status_offline]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._aplicar_filtros()

    def _set_filtro_bloco(self, novo_bloco: str):
        self.filtro_bloco_ativo = novo_bloco
        self._atualizar_pills_blocos()
        self._aplicar_filtros()

    def _renderizar_grade_ramais(self):
        # Limpar cartões antigos da grade
        while self.grid_ramais.count() > 0:
            item = self.grid_ramais.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.cartoes_map.clear()

        # Filtrar
        busca = self.edit_busca.text().strip().lower()
        ramais_visiveis = []

        for r in self.todos_os_ramais:
            if self.filtro_bloco_ativo != "TODOS" and r.get("bloco") != self.filtro_bloco_ativo:
                continue
            if self.filtro_status_ativo != "TODOS" and r.get("status") != self.filtro_status_ativo:
                continue
            if busca:
                texto_item = f"{r.get('descricao', '')} {r.get('ip', '')} {r.get('mac_cisco', '')} {r.get('setor', '')} {r.get('bloco', '')} {r.get('modelo', '')}".lower()
                if busca not in texto_item:
                    continue
            ramais_visiveis.append(r)

        # Montar grade em 4 colunas (ou 3 se a janela for menor)
        cols_max = 4 if self.width() >= 1200 else 3
        row = 0
        col = 0

        for r_dict in ramais_visiveis:
            card = RamalCard(r_dict, parent_window=self)
            self.cartoes_map[r_dict["id"]] = card
            self.grid_ramais.addWidget(card, row, col)

            col += 1
            if col >= cols_max:
                col = 0
                row += 1

    def _aplicar_filtros(self):
        self._renderizar_grade_ramais()

    # =========================================================================
    # AÇÕES SENSÍVEIS E AUTENTICAÇÃO
    # =========================================================================

    def _executar_acao_sensivel(self, motivo: str, acao_sucesso):
        is_admin = False
        if self.usuario_atual:
            perfil = getattr(self.usuario_atual, "perfil", None)
            if perfil in [PerfilUsuario.ADMINISTRADOR.value, "ADMINISTRADOR"]:
                is_admin = True

        if is_admin:
            acao_sucesso()
        else:
            dlg = LoginDialog(motivo=motivo, parent=self)
            if dlg.exec() == LoginDialog.DialogCode.Accepted:
                self.usuario_atual = dlg.usuario_autenticado
                self._atualizar_botao_admin()
                acao_sucesso()

    def _toggle_admin(self):
        if self.usuario_atual:
            if QMessageBox.question(self, "Sair", "Deseja encerrar o modo Administrador e voltar ao monitoramento livre?") == QMessageBox.StandardButton.Yes:
                self.usuario_atual = None
                self._atualizar_botao_admin()
        else:
            dlg = LoginDialog(motivo="Autenticação Geral de Administrador", parent=self)
            if dlg.exec() == LoginDialog.DialogCode.Accepted:
                self.usuario_atual = dlg.usuario_autenticado
                self._atualizar_botao_admin()

    def _atualizar_botao_admin(self):
        if self.usuario_atual:
            nome = getattr(self.usuario_atual, "nome", "Wagner")
            self.btn_admin.setText(f"👤 {nome} (Sair)")
            self.btn_admin.setObjectName("btnNavAdminLogged")
        else:
            self.btn_admin.setText("🔒 Admin")
            self.btn_admin.setObjectName("btnNavAdmin")

        self.btn_admin.style().unpolish(self.btn_admin)
        self.btn_admin.style().polish(self.btn_admin)

    def _abrir_modal_exe(self):
        msg = (
            "📦 HAOC VoIP Monitor Enterprise - Executável Standalone para Windows\n\n"
            "Para gerar ou rodar o executável nativo na sua máquina Windows:\n\n"
            "1. Execute o arquivo auxiliar 'build_windows.bat' incluso na raiz do projeto.\n"
            "2. Ele gerará o binário 'dist/HAOC_VoIP_Monitor.exe' totalmente independente.\n"
            "3. O aplicativo abre diretamente nesta mesma interface NOC, sem pedir senha inicial!\n"
        )
        QMessageBox.information(self, "Gerar / Compilar Executável .EXE", msg)

    def _novo_ramal(self):
        dlg = RamalDialog(usuario_atual=self.usuario_atual, parent=self)
        if dlg.exec():
            self._carregar_dados_interface()

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
        if QMessageBox.question(self, "Confirmar", f"Deseja remover o ramal #{ramal_id} do monitoramento?") == QMessageBox.StandardButton.Yes:
            with db.session_scope() as session:
                r = session.query(Ramal).filter(Ramal.id == ramal_id).first()
                if r:
                    r.ativo = False
            self._carregar_dados_interface()

    def _abrir_importacao(self):
        dlg = ImportDialog(usuario_atual=self.usuario_atual, parent=self)
        if dlg.exec():
            self._carregar_dados_interface()

    def _abrir_incidentes(self):
        dlg = IncidentesDialog(usuario_atual=self.usuario_atual, parent=self)
        dlg.exec()

    # =========================================================================
    # PING E VARREDURA CONCORRENTE
    # =========================================================================

    def _iniciar_varredura(self):
        if monitor_engine.em_execucao:
            QMessageBox.information(self, "Aviso", "A varredura de ICMP já está em andamento.")
            return

        signals.scan_started.emit()

        def _worker():
            try:
                resumo = monitor_engine.executar_varredura()
                signals.scan_finished.emit(resumo)
            except Exception:
                signals.scan_canceled.emit()

        threading.Thread(target=_worker, daemon=True).start()

    def disparar_ping_individual(self, ramal_id: int):
        self.lbl_sb_msg.setText(f"Enviando pacote ICMP para ramal #{ramal_id}...")

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

    def _on_scan_started(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.lbl_sb_msg.setText("Varredura geral de ICMP em andamento...")

    def _on_scan_progress(self, concluidos, total, msg):
        if total > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int((concluidos / total) * 100))
        self.lbl_sb_msg.setText(msg)

    def _on_scan_finished(self, resumo):
        self.progress_bar.setVisible(False)
        on = resumo.get("online", 0)
        off = resumo.get("offline", 0)
        self.lbl_sb_msg.setText(
            f"Varredura concluída com sucesso às {datetime.now().strftime('%H:%M:%S')} (Online: {on}, Offline: {off})"
        )
        self._carregar_dados_interface()

    def _on_scan_canceled(self):
        self.progress_bar.setVisible(False)
        self.lbl_sb_msg.setText("Varredura cancelada.")

    def _on_ping_result(self, ramal_id: int, sucesso: bool, latencia: float, erro: str):
        if sucesso:
            QMessageBox.information(self, "Resultado do Ping", f"✅ Conexão estabelecida com sucesso!\nLatência: {latencia:.1f} ms")
        else:
            QMessageBox.warning(self, "Resultado do Ping", f"❌ Host Inalcançável!\nMotivo: {erro or 'Tempo limite de requisição esgotado'}")
        self._carregar_dados_interface()
