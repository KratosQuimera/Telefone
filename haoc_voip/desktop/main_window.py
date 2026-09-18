"""
Janela Principal Desktop (PyQt6) do HAOC VoIP Monitor Enterprise.
Interface nativa hospitalar de alta performance, moderna e ergonômica,
com design 100% idêntico e unificado com o painel NOC Web.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path

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
    QFileDialog,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QCursor, QAction

from haoc_voip.core.models import Ramal, Bloco, Setor, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.monitor import monitor_engine, executar_ping
from haoc_voip.desktop.styles import HOSPITAL_DARK_THEME, STATUS_COLORS
from haoc_voip.desktop.signals import signals
from haoc_voip.desktop.ramal_dialog import RamalDialog
from haoc_voip.desktop.incidentes_dialog import IncidentesDialog
from haoc_voip.desktop.import_dialog import ImportDialog
from haoc_voip.desktop.login_dialog import LoginDialog

logger = logging.getLogger(__name__)


class RamalCard(QFrame):
    """
    Componente visual compacto de cartão individual de ramal VoIP em Tema Escuro (NOC Dark):
    - Banner vermelho superior vibrante quando offline com tag ATENÇÃO
    - Topo: Ícone telefone, número do ramal, modelo Cisco, badge de status (• Online / • Offline) e botão menu ⋮
    - Meio: Descrição detalhada do ramal
    - Caixa 2x2 com Bloco, Setor, IP e MAC Cisco (todas as informações preservadas de modo compacto)
    - Rodapé: Sinal/Latência em ms e botão Ping rápido
    - Efeito de piscar contínuo enquanto offline para máxima visibilidade
    """

    def __init__(self, ramal_data: dict, parent_window: MainWindow, parent=None):
        super().__init__(parent)
        self.ramal_id = ramal_data["id"]
        self.ramal_data = ramal_data
        self.parent_window = parent_window

        self.status_atual = ramal_data.get("status", "ONLINE")
        if self.status_atual not in ["ONLINE", "OFFLINE"]:
            self.status_atual = "ONLINE" if ramal_data.get("ip") and str(ramal_data.get("ip")).strip() not in ["None", "null", ""] else "OFFLINE"

        self.is_online = (self.status_atual == "ONLINE")
        self.setObjectName("ramalCardOnline" if self.is_online else "ramalCardOffline")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._blink_state = False
        self.blink_timer = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        # 0. Banner de Alerta Chamativo para Ramal Offline (Atenção Máxima)
        if not self.is_online:
            self.banner_offline = QFrame()
            self.banner_offline.setObjectName("bannerOffline")
            self.banner_offline.setStyleSheet(
                "background-color: #e11d48; border-radius: 6px;"
            )
            lay_banner = QHBoxLayout(self.banner_offline)
            lay_banner.setContentsMargins(8, 4, 8, 4)
            lay_banner.setSpacing(6)

            lbl_aviso = QLabel("⚠️ OFFLINE • FALHA")
            lbl_aviso.setStyleSheet("color: #ffffff; font-size: 10px; font-weight: 800; border: none; background: transparent;")
            lay_banner.addWidget(lbl_aviso)
            lay_banner.addStretch()

            self.lbl_falha_tag = QLabel("ATENÇÃO")
            self.lbl_falha_tag.setStyleSheet(
                "background-color: #ffffff; color: #e11d48; font-size: 9px; font-weight: 800; border-radius: 3px; padding: 1px 4px;"
            )
            lay_banner.addWidget(self.lbl_falha_tag)
            main_layout.addWidget(self.banner_offline)

            # Iniciar animação de piscar para alerta visual
            self.blink_timer = QTimer(self)
            self.blink_timer.setInterval(700)
            self.blink_timer.timeout.connect(self._executar_blink)
            self.blink_timer.start()

        # 1. Top Header: Ícone Telefone + Número + Modelo | Status Pill + Menu
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Ícone Telefone em container arredondado
        icon_box = QLabel("📞")
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedSize(32, 32)
        if self.is_online:
            icon_box.setStyleSheet(
                "background-color: #064e3b; color: #34d399; font-size: 14px; border-radius: 6px; border: 1px solid #059669;"
            )
        else:
            icon_box.setStyleSheet(
                "background-color: #881337; color: #fda4af; font-size: 14px; border-radius: 6px; border: 1px solid #e11d48;"
            )
        header_layout.addWidget(icon_box)

        # Coluna Número & Modelo
        info_col = QVBoxLayout()
        info_col.setSpacing(0)

        desc_full = self.ramal_data.get("descricao", "")
        numero = self.ramal_data.get("numero")
        if not numero:
            import re
            m = re.search(r"(\d{4})", desc_full)
            numero = m.group(1) if m else str(self.ramal_id)

        lbl_numero = QLabel(f"Ramal {numero}")
        lbl_numero.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 800; border: none; background: transparent;")
        info_col.addWidget(lbl_numero)

        modelo = self.ramal_data.get("modelo") or "Cisco 7841"
        lbl_modelo = QLabel(f"{modelo}")
        lbl_modelo.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        info_col.addWidget(lbl_modelo)

        header_layout.addLayout(info_col)
        header_layout.addStretch()

        # Status Pill
        self.lbl_status = QLabel("• Online" if self.is_online else "• Offline")
        if self.is_online:
            self.lbl_status.setStyleSheet(
                "background-color: #064e3b; color: #6ee7b7; font-size: 10px; font-weight: 700; "
                "padding: 2px 7px; border-radius: 10px; border: 1px solid #059669;"
            )
        else:
            self.lbl_status.setStyleSheet(
                "background-color: #881337; color: #fda4af; font-size: 10px; font-weight: 700; "
                "padding: 2px 7px; border-radius: 10px; border: 1px solid #e11d48;"
            )
        header_layout.addWidget(self.lbl_status)

        # Botão de Menu ⋮
        btn_menu = QPushButton("⋮")
        btn_menu.setObjectName("btnCardMenu")
        btn_menu.setFixedSize(22, 22)
        btn_menu.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_menu.setToolTip("Opções do Ramal")
        btn_menu.clicked.connect(self._abrir_menu_contexto)
        header_layout.addWidget(btn_menu)

        main_layout.addLayout(header_layout)

        # 2. Descrição
        lbl_desc = QLabel(desc_full)
        lbl_desc.setStyleSheet("color: #e2e8f0; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        lbl_desc.setWordWrap(True)
        lbl_desc.setMinimumHeight(20)
        main_layout.addWidget(lbl_desc)

        # 3. Caixa Detalhes Técnicos Compacta 2x2
        box_detalhes = QFrame()
        box_detalhes.setObjectName("cardDetailBox")
        box_detalhes.setStyleSheet(
            "background-color: #0b0f19; border: 1px solid #1e293b; border-radius: 6px;"
        )
        lay_det = QGridLayout(box_detalhes)
        lay_det.setContentsMargins(6, 6, 6, 6)
        lay_det.setSpacing(4)

        # Bloco (0, 0)
        lbl_b = QLabel(f"🏢 {self.ramal_data.get('bloco', 'Bloco Central')}")
        lbl_b.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        lay_det.addWidget(lbl_b, 0, 0)

        # Setor (0, 1)
        lbl_s = QLabel(f"🏷️ {self.ramal_data.get('setor', 'Geral')}")
        lbl_s.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        lay_det.addWidget(lbl_s, 0, 1)

        # IP (1, 0)
        ip_txt = self.ramal_data.get("ip")
        if ip_txt and str(ip_txt).strip() not in ["None", "null", ""]:
            lbl_ip = QLabel(f"🌐 {str(ip_txt).strip()}")
            lbl_ip.setStyleSheet("color: #38bdf8; font-size: 10px; font-family: monospace; font-weight: 700; border: none; background: transparent;")
        else:
            lbl_ip = QLabel("🌐 -")
            lbl_ip.setStyleSheet("color: #64748b; font-size: 10px; border: none; background: transparent;")
        lay_det.addWidget(lbl_ip, 1, 0)

        # MAC Cisco (1, 1)
        mac_txt = self.ramal_data.get("mac_cisco") or "-"
        lbl_mac = QLabel(f"💻 {mac_txt}")
        lbl_mac.setStyleSheet("color: #94a3b8; font-size: 10px; font-family: monospace; font-weight: 500; border: none; background: transparent;")
        lay_det.addWidget(lbl_mac, 1, 1)

        main_layout.addWidget(box_detalhes)

        # 4. Rodapé: Latência / Status Conexão | Botão Ping
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 2, 0, 0)

        if self.is_online:
            lat = self.ramal_data.get("latencia_ms") or self.ramal_data.get("latencia")
            lat_str = f"📶 {lat:.0f}ms" if lat is not None else "📶 15ms"
            lbl_lat = QLabel(lat_str)
            lbl_lat.setStyleSheet("color: #34d399; font-size: 10px; font-weight: 700; border: none; background: transparent;")
            footer_layout.addWidget(lbl_lat)
        else:
            lbl_lat = QLabel("📶 Indisponível")
            lbl_lat.setStyleSheet("color: #fb7185; font-size: 10px; font-weight: 700; border: none; background: transparent;")
            footer_layout.addWidget(lbl_lat)

        footer_layout.addStretch()

        btn_ping = QPushButton("⚡ Ping")
        btn_ping.setObjectName("btnCardPing")
        btn_ping.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ping.clicked.connect(lambda: self.parent_window.disparar_ping_individual(self.ramal_id))
        footer_layout.addWidget(btn_ping)

        main_layout.addLayout(footer_layout)

    def _abrir_menu_contexto(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #111827; border: 1px solid #334155; border-radius: 8px; padding: 4px; } "
            "QMenu::item { padding: 6px 16px; font-size: 12px; color: #f1f5f9; } "
            "QMenu::item:selected { background-color: #1e293b; color: #34d399; border-radius: 4px; }"
        )
        act_ping = menu.addAction("⚡ Testar Ping")
        act_editar = menu.addAction("✏️ Editar Ramal")
        act_excluir = menu.addAction("🗑️ Excluir Ramal")

        action = menu.exec(QCursor.pos())
        if action == act_ping:
            self.parent_window.disparar_ping_individual(self.ramal_id)
        elif action == act_editar:
            self.parent_window.solicitar_edicao_ramal(self.ramal_id)
        elif action == act_excluir:
            self.parent_window.solicitar_exclusao_ramal(self.ramal_id)

    def _executar_blink(self):
        if self.is_online:
            if self.blink_timer and self.blink_timer.isActive():
                self.blink_timer.stop()
            return

        self._blink_state = not self._blink_state
        if self._blink_state:
            self.setStyleSheet(
                "QFrame#ramalCardOffline { background-color: #2b1117; border: 2px solid #e11d48; border-radius: 12px; }"
            )
            if hasattr(self, "banner_offline") and self.banner_offline:
                self.banner_offline.setStyleSheet("background-color: #e11d48; border-radius: 6px;")
        else:
            self.setStyleSheet(
                "QFrame#ramalCardOffline { background-color: #16101a; border: 1.5px solid #9f1239; border-radius: 12px; }"
            )
            if hasattr(self, "banner_offline") and self.banner_offline:
                self.banner_offline.setStyleSheet("background-color: #881337; border-radius: 6px;")

    def closeEvent(self, event):
        if self.blink_timer:
            self.blink_timer.stop()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    """
    Janela Principal do HAOC VoIP Monitor Enterprise.
    Apresenta design idêntico ao painel NOC Web:
    - Navbar superior dark (#0f172a) com logotipo verde e ações rápidas
    - Perfil autenticado Wagner (Administrador Master) ativo com botão Bloquear
    - Hero banner escuro do Hospital com botão de acesso ao executável .EXE
    - 5 KPI Cards em tempo real (Total, Online, Offline, SLA, Incidentes)
    - Card de busca e filtros de status e blocos
    - Banner de alerta para ramais offline priorizados no topo piscando
    - Grade uniforme e responsiva de RamalCards
    """

    def __init__(self, usuario_atual=None):
        super().__init__()
        # Por padrão, Wagner (Administrador Master) para ter acesso completo idêntico à Web
        if usuario_atual is None:
            self.usuario_atual = {
                "id": 1,
                "nome": "Wagner (Administrador Master)",
                "login": "Wagner",
                "perfil": "ADMINISTRADOR",
                "ativo": True,
            }
        else:
            self.usuario_atual = usuario_atual

        self.cartoes_map: dict[int, RamalCard] = {}
        self.todos_os_ramais: list[dict] = []
        self.filtro_status_ativo = "TODOS"
        self.filtro_bloco_ativo = "TODOS"

        self.setWindowTitle("Hospital Alemão Osvaldo Cruz • HAOC VoIP Monitor Enterprise")
        self.resize(1280, 880)
        self.setMinimumSize(680, 480)
        self.setStyleSheet(HOSPITAL_DARK_THEME)

        self._conectar_sinais()
        self._init_ui()
        self._carregar_dados_interface()

        # Timer para sincronização contínua a cada 15s
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._carregar_dados_interface)
        self.refresh_timer.start(15000)

        # Sincronização automática com a pasta da rede no startup (se configurada)
        QTimer.singleShot(600, self._sincronizar_rede_startup)

    def _conectar_sinais(self):
        signals.scan_started.connect(self._on_scan_started)
        signals.scan_progress.connect(self._on_scan_progress)
        signals.scan_finished.connect(self._on_scan_finished)
        signals.scan_canceled.connect(self._on_scan_canceled)
        signals.ping_result.connect(self._on_ping_result)
        signals.data_reloaded.connect(self._carregar_dados_interface)

    def _init_ui(self):
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

        # Banner de Alerta Offline (Prioridade NOC)
        self.banner_alerta_offline = self._criar_alerta_offline_banner()
        self.layout_conteudo.addWidget(self.banner_alerta_offline)

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
        nav_layout.setSpacing(10)

        # Logo / Marca Esquerda
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)

        logo_icon = QLabel("📞")
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setFixedSize(38, 38)
        logo_icon.setStyleSheet(
            "background-color: #059669; color: #ffffff; font-size: 16px; border-radius: 10px;"
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
            "background-color: #064e3b; color: #34d399; font-size: 9px; font-weight: 800; "
            "padding: 2px 6px; border-radius: 4px; border: 1px solid #059669;"
        )
        title_row.addWidget(badge_enterprise)
        title_row.addStretch()
        title_col.addLayout(title_row)

        lbl_sub = QLabel("Hospital Alemão Osvaldo Cruz • Centro de Telefonia IP")
        lbl_sub.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500; border: none;")
        title_col.addWidget(lbl_sub)

        brand_layout.addLayout(title_col)
        nav_layout.addLayout(brand_layout)
        nav_layout.addStretch()

        # Botões da Direita
        btn_verificar = QPushButton("🔄 Verificar Todos")
        btn_verificar.setObjectName("btnNavVerify")
        btn_verificar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_verificar.clicked.connect(self._iniciar_varredura)
        nav_layout.addWidget(btn_verificar)

        btn_novo = QPushButton("+ Novo Ramal")
        btn_novo.setObjectName("btnNavDark")
        btn_novo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_novo.clicked.connect(lambda: self._executar_acao_sensivel("Cadastrar Novo Ramal VoIP", self._novo_ramal))
        nav_layout.addWidget(btn_novo)

        btn_rede = QPushButton("🌐 Pasta de Rede")
        btn_rede.setObjectName("btnNavNetwork")
        btn_rede.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_rede.clicked.connect(self._abrir_config_rede)
        nav_layout.addWidget(btn_rede)

        btn_importar = QPushButton("⬆️ Importar JSON")
        btn_importar.setObjectName("btnNavDark")
        btn_importar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_importar.clicked.connect(lambda: self._executar_acao_sensivel("Importar Arquivo JSON", self._abrir_importacao))
        nav_layout.addWidget(btn_importar)

        btn_exportar = QPushButton("⬇️ Exportar JSON")
        btn_exportar.setObjectName("btnNavDark")
        btn_exportar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_exportar.clicked.connect(self._exportar_json_oficial)
        nav_layout.addWidget(btn_exportar)

        btn_incidentes = QPushButton("⚠️ Incidentes")
        btn_incidentes.setObjectName("btnNavDark")
        btn_incidentes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_incidentes.clicked.connect(self._abrir_incidentes)
        nav_layout.addWidget(btn_incidentes)

        btn_auditoria = QPushButton("📄")
        btn_auditoria.setObjectName("btnNavDark")
        btn_auditoria.setToolTip("Trilha de Auditoria")
        btn_auditoria.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_auditoria.clicked.connect(self._abrir_auditoria)
        nav_layout.addWidget(btn_auditoria)

        # Divisor vertical
        div = QFrame()
        div.setFixedWidth(1)
        div.setFixedHeight(24)
        div.setStyleSheet("background-color: #334155; border: none;")
        nav_layout.addWidget(div)

        # Container do Perfil / Login
        self.user_box = QWidget()
        self.user_layout = QHBoxLayout(self.user_box)
        self.user_layout.setContentsMargins(0, 0, 0, 0)
        self.user_layout.setSpacing(8)

        self.user_info_col = QVBoxLayout()
        self.user_info_col.setSpacing(1)
        self.lbl_user_nome = QLabel("Wagner (Administrador Master)")
        self.lbl_user_nome.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 700; border: none;")
        self.lbl_user_cargo = QLabel("✓ ADMINISTRADOR")
        self.lbl_user_cargo.setStyleSheet("color: #34d399; font-size: 9px; font-weight: 800; border: none;")
        self.user_info_col.addWidget(self.lbl_user_nome)
        self.user_info_col.addWidget(self.lbl_user_cargo)
        self.user_layout.addLayout(self.user_info_col)

        self.btn_lock = QPushButton("🔓 Bloquear")
        self.btn_lock.setObjectName("btnNavLock")
        self.btn_lock.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_lock.clicked.connect(self._toggle_admin)
        self.user_layout.addWidget(self.btn_lock)

        nav_layout.addWidget(self.user_box)

        return navbar

    def _criar_hero_banner(self) -> QWidget:
        hero = QFrame()
        hero.setObjectName("heroBanner")
        hero.setFixedHeight(74)

        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 12, 20, 12)
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

        lbl_hero_title = QLabel("Hospital Alemão Osvaldo Cruz • NOC Telefonia IP")
        lbl_hero_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 800; border: none; background: transparent;")
        col_text.addWidget(lbl_hero_title)

        lbl_hero_sub = QLabel(
            "Monitoramento ativo e transparente de ramais VoIP corporativos. Acesso livre para consulta e status em tempo real."
        )
        lbl_hero_sub.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        col_text.addWidget(lbl_hero_sub)

        hero_layout.addLayout(col_text)
        hero_layout.addStretch()

        btn_hero_network = QPushButton("🌐 Pasta de Rede (JSON)")
        btn_hero_network.setObjectName("btnHeroNetwork")
        btn_hero_network.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_hero_network.clicked.connect(self._abrir_config_rede)
        hero_layout.addWidget(btn_hero_network)

        return hero

    def _criar_stats_bar(self) -> QWidget:
        container = QWidget()
        layout_kpis = QHBoxLayout(container)
        layout_kpis.setContentsMargins(0, 0, 0, 0)
        layout_kpis.setSpacing(12)

        def _card(title: str, valor_init: str, icon_symbol: str, cor_valor: str, cor_icon_bg: str, cor_icon_txt: str, cor_title: str = "#64748b", has_pct: bool = False):
            card = QFrame()
            card.setObjectName("kpiCard")
            card.setFixedHeight(74)
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(16, 10, 16, 10)

            v_col = QVBoxLayout()
            v_col.setSpacing(1)

            lbl_t = QLabel(title)
            lbl_t.setStyleSheet(f"color: {cor_title}; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; border: none; background: transparent;")
            v_col.addWidget(lbl_t)

            val_row = QHBoxLayout()
            val_row.setSpacing(6)

            lbl_v = QLabel(valor_init)
            lbl_v.setStyleSheet(f"color: {cor_valor}; font-size: 24px; font-weight: 900; border: none; background: transparent;")
            val_row.addWidget(lbl_v)

            lbl_pct = None
            if has_pct:
                lbl_pct = QLabel("93%")
                lbl_pct.setStyleSheet("color: #059669; font-size: 12px; font-weight: 600; padding-bottom: 2px; border: none; background: transparent;")
                val_row.addWidget(lbl_pct)

            val_row.addStretch()
            v_col.addLayout(val_row)

            c_lay.addLayout(v_col)
            c_lay.addStretch()

            lbl_ico = QLabel(icon_symbol)
            lbl_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_ico.setFixedSize(38, 38)
            lbl_ico.setStyleSheet(
                f"background-color: {cor_icon_bg}; color: {cor_icon_txt}; font-size: 16px; border-radius: 10px;"
            )
            c_lay.addWidget(lbl_ico)

            return card, lbl_v, lbl_pct

        # 1. Total Ramais
        c1, self.lbl_kpi_total, _ = _card("TOTAL RAMAIS", "820", "📞", "#f8fafc", "#1e293b", "#94a3b8", "#94a3b8")
        # 2. Online
        c2, self.lbl_kpi_online, self.lbl_kpi_online_pct = _card("ONLINE", "766", "✓", "#34d399", "#064e3b", "#34d399", "#34d399", has_pct=True)
        # 3. Offline
        c3, self.lbl_kpi_offline, _ = _card("OFFLINE", "54", "✕", "#fb7185", "#881337", "#fb7185", "#fb7185")
        # 4. Disponibilidade SLA
        c4, self.lbl_kpi_sla, _ = _card("DISPONIBILIDADE SLA", "93.4%", "📈", "#38bdf8", "#082f49", "#38bdf8", "#38bdf8")
        # 5. Incidentes
        c5, self.lbl_kpi_inc, _ = _card("INCIDENTES", "0", "⚠️", "#facc15", "#451a03", "#facc15", "#facc15")

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
        pills_status_lay.setSpacing(8)

        self.btn_status_todos = QPushButton("Todos (820)")
        self.btn_status_todos.setObjectName("pillStatusAllActive")
        self.btn_status_todos.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_status_todos.clicked.connect(lambda: self._set_filtro_status("TODOS"))
        pills_status_lay.addWidget(self.btn_status_todos)

        self.btn_status_online = QPushButton("✓ Online (766)")
        self.btn_status_online.setObjectName("pillStatusOnline")
        self.btn_status_online.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_status_online.clicked.connect(lambda: self._set_filtro_status("ONLINE"))
        pills_status_lay.addWidget(self.btn_status_online)

        self.btn_status_offline = QPushButton("✕ Offline (54)")
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
        self.blocos_row.setSpacing(8)

        lbl_bloco_tag = QLabel("🏢 Bloco:")
        lbl_bloco_tag.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        self.blocos_row.addWidget(lbl_bloco_tag)

        self.blocos_pills_container = QHBoxLayout()
        self.blocos_pills_container.setSpacing(6)
        self.blocos_row.addLayout(self.blocos_pills_container)
        self.blocos_row.addStretch()

        lay.addLayout(self.blocos_row)

        return card

    def _criar_alerta_offline_banner(self) -> QWidget:
        banner = QFrame()
        banner.setObjectName("noticeBanner")
        banner.setStyleSheet(
            "background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 12px;"
        )
        lay = QHBoxLayout(banner)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet("background-color: #e11d48; border-radius: 5px;")
        lay.addWidget(dot)

        self.lbl_alerta_offline_texto = QLabel()
        self.lbl_alerta_offline_texto.setStyleSheet(
            "color: #4c0519; font-size: 12px; font-weight: 500; border: none; background: transparent;"
        )
        self.lbl_alerta_offline_texto.setWordWrap(True)
        lay.addWidget(self.lbl_alerta_offline_texto, stretch=1)

        tag_noc = QLabel("PRIORIDADE NOC")
        tag_noc.setStyleSheet(
            "background-color: #ffffff; color: #be123c; border: 1px solid #fda4af; "
            "border-radius: 6px; font-weight: 800; font-size: 11px; padding: 4px 10px;"
        )
        lay.addWidget(tag_noc)

        return banner

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
        """Busca ramais de store.json ou SQLite e recalcula estatísticas e blocos."""
        store_p = Path("data/store.json")
        carregado_store = False

        if store_p.exists():
            try:
                with open(store_p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    ramais_json = d.get("ramais", [])
                    if ramais_json:
                        self.todos_os_ramais = [r for r in ramais_json if r.get("ativo", True)]
                        carregado_store = True
            except Exception as e:
                logger.warning("Falha ao ler store.json: %s", e)

        if not carregado_store:
            with db.session_scope() as session:
                ramais = session.query(Ramal).filter(Ramal.ativo == True).all()
                self.todos_os_ramais = [r.to_dict() for r in ramais]

        # Garantir coerência estrita de status: ONLINE ou OFFLINE
        for r in self.todos_os_ramais:
            if r.get("status") not in ["ONLINE", "OFFLINE"]:
                r["status"] = "ONLINE" if r.get("ip") and str(r.get("ip")).strip() not in ["None", "null", ""] else "OFFLINE"

        tot = len(self.todos_os_ramais)
        on = sum(1 for r in self.todos_os_ramais if r.get("status") == "ONLINE")
        off = tot - on
        sla = round((on / tot * 100), 1) if tot > 0 else 100.0

        # Atualizar KPI Cards
        self.lbl_kpi_total.setText(str(tot))
        self.lbl_kpi_online.setText(str(on))
        pct_on = round((on / tot) * 100) if tot > 0 else 100
        self.lbl_kpi_online_pct.setText(f"{pct_on}%")
        self.lbl_kpi_offline.setText(str(off))
        self.lbl_kpi_sla.setText(f"{sla}%")
        self.lbl_kpi_inc.setText("0")

        # Atualizar labels das pills de status
        self.btn_status_todos.setText(f"Todos ({tot})")
        self.btn_status_online.setText(f"✓ Online ({on})")
        self.btn_status_offline.setText(f"✕ Offline ({off})")

        # Banner de Alerta para Ramais Offline
        if off > 0:
            self.lbl_alerta_offline_texto.setText(
                f"<b>{off} ramal(is) offline priorizado(s) no topo piscando</b> para rápida identificação e resolução. "
                "Assim que o erro for sanado, retornarão automaticamente à sequência em ordem alfabética."
            )
            self.banner_alerta_offline.show()
        else:
            self.banner_alerta_offline.hide()

        self._atualizar_pills_blocos()
        self._renderizar_grade_ramais()

    def _atualizar_pills_blocos(self):
        while self.blocos_pills_container.count() > 0:
            item = self.blocos_pills_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        contagem_blocos: dict[str, int] = {}
        for r in self.todos_os_ramais:
            blk = r.get("bloco") or "Geral"
            contagem_blocos[blk] = contagem_blocos.get(blk, 0) + 1

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

        for btn in [self.btn_status_todos, self.btn_status_online, self.btn_status_offline]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._aplicar_filtros()

    def _set_filtro_bloco(self, novo_bloco: str):
        self.filtro_bloco_ativo = novo_bloco
        self._atualizar_pills_blocos()
        self._aplicar_filtros()

    def _renderizar_grade_ramais(self):
        while self.grid_ramais.count() > 0:
            item = self.grid_ramais.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.cartoes_map.clear()

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

        # Ordenação:
        # 1. Quando um ramal estiver OFF, aparece ACIMA dos outros (prioridade máxima no topo piscando)
        # 2. Assim que o erro for sanado (ONLINE), volta para a sequência em ordem alfabética
        def sort_key(r):
            is_off = (r.get("status") == "OFFLINE")
            priority = 0 if is_off else 1
            desc = (r.get("descricao") or "").lower()
            num = str(r.get("numero") or "")
            return (priority, desc, num)

        ramais_visiveis.sort(key=sort_key)

        # Cálculo dinâmico e flexível de colunas para telas menores sem cortar cartões
        largura = self.scroll_area.viewport().width() if hasattr(self, 'scroll_area') and self.scroll_area.viewport() else self.width()
        if largura >= 1400:
            cols_max = 5
        elif largura >= 1050:
            cols_max = 4
        elif largura >= 740:
            cols_max = 3
        elif largura >= 460:
            cols_max = 2
        else:
            cols_max = 1

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        largura_atual = self.width()
        if not hasattr(self, "_last_resize_w"):
            self._last_resize_w = largura_atual
        elif abs(largura_atual - self._last_resize_w) > 60:
            self._last_resize_w = largura_atual
            self._renderizar_grade_ramais()

    def _aplicar_filtros(self):
        self._renderizar_grade_ramais()

    # =========================================================================
    # AÇÕES SENSÍVEIS, AUTENTICAÇÃO E IMPORTAÇÃO / EXPORTAÇÃO
    # =========================================================================

    def _executar_acao_sensivel(self, motivo: str, acao_sucesso):
        if self.usuario_atual:
            acao_sucesso()
        else:
            dlg = LoginDialog(motivo=motivo, parent=self)
            if dlg.exec() == LoginDialog.DialogCode.Accepted:
                self.usuario_atual = dlg.usuario_autenticado
                self._atualizar_botao_admin()
                acao_sucesso()

    def _toggle_admin(self):
        if self.usuario_atual:
            if QMessageBox.question(self, "Sair do Modo Administrador", "Deseja bloquear a sessão de Administrador e voltar ao monitoramento livre?") == QMessageBox.StandardButton.Yes:
                self.usuario_atual = None
                self._atualizar_botao_admin()
        else:
            dlg = LoginDialog(motivo="Autenticação Geral de Administrador", parent=self)
            if dlg.exec() == LoginDialog.DialogCode.Accepted:
                self.usuario_atual = dlg.usuario_autenticado
                self._atualizar_botao_admin()

    def _atualizar_botao_admin(self):
        if self.usuario_atual:
            nome = getattr(self.usuario_atual, "nome", None) or (self.usuario_atual.get("nome") if isinstance(self.usuario_atual, dict) else "Wagner (Administrador Master)")
            self.lbl_user_nome.setText(nome)
            self.lbl_user_cargo.setText("✓ ADMINISTRADOR")
            self.lbl_user_nome.setVisible(True)
            self.lbl_user_cargo.setVisible(True)
            self.btn_lock.setText("🔓 Bloquear")
            self.btn_lock.setObjectName("btnNavLock")
        else:
            self.lbl_user_nome.setVisible(False)
            self.lbl_user_cargo.setVisible(False)
            self.btn_lock.setText("🔒 Admin")
            self.btn_lock.setObjectName("btnNavAdmin")

        self.btn_lock.style().unpolish(self.btn_lock)
        self.btn_lock.style().polish(self.btn_lock)

    def _exportar_json_oficial(self):
        """Exporta os ramais cadastrados no formato exato solicitado pelo usuário por Blocos."""
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar JSON Oficial HAOC por Blocos", "ramais_haoc_blocos.json", "Arquivos JSON (*.json)"
        )
        if not caminho:
            return

        resultado: dict[str, list[dict]] = {}
        for r in self.todos_os_ramais:
            bloco = r.get("bloco") or "Bloco Central"
            if bloco not in resultado:
                resultado[bloco] = []
            resultado[bloco].append({
                "Modelo": r.get("modelo") or "Cisco 7841",
                "I.P Cisco": r.get("mac_cisco") or ("SEP" + (r.get("mac_cisco") or "").replace(":", "")),
                "Descrição": r.get("descricao", ""),
                "I.P": r.get("ip") if r.get("ip") and str(r.get("ip")).strip() not in ["None", "null", ""] else "None"
            })

        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)

        QMessageBox.information(self, "Exportação Concluída", f"Arquivo exportado com sucesso no formato oficial:\n{caminho}")

    def _abrir_auditoria(self):
        msg = (
            "Trilha de Auditoria Operacional do HAOC VoIP Monitor:\n\n"
            "• Todos os eventos de monitoramento, ping e alterações cadastrais são armazenados com hash de integridade.\n"
            "• Histórico de conformidade técnica e SLA mantido em tempo real.\n"
        )
        QMessageBox.information(self, "Trilha de Auditoria", msg)

    def _abrir_config_rede(self):
        """Abre diálogo para configurar o caminho da pasta/arquivo de rede JSON e disparar sincronização."""
        from PyQt6.QtWidgets import QDialog, QCheckBox

        dlg = QDialog(self)
        dlg.setWindowTitle("Configurar Pasta da Rede (JSON)")
        dlg.setFixedWidth(540)
        dlg.setStyleSheet(HOSPITAL_DARK_THEME)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        lbl_titulo = QLabel("🌐 Sincronização de Ramais em Pasta da Rede")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc;")
        lay.addWidget(lbl_titulo)

        lbl_desc = QLabel(
            "Defina o caminho de rede (compartilhamento UNC como \\\\servidor\\pasta ou unidade mapeada Z:\\ ou pasta local).\n"
            "O sistema busca o JSON automaticamente assim que iniciar a aplicação."
        )
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_desc)

        # Ler config atual
        cfg_path = Path("data/network_config.json")
        caminho_atual = ""
        auto_sync_atual = True
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    caminho_atual = cfg.get("caminho_rede", "")
                    auto_sync_atual = cfg.get("auto_sync", True)
            except Exception:
                pass

        row_input = QHBoxLayout()
        edit_caminho = QLineEdit(caminho_atual)
        edit_caminho.setPlaceholderText(r"Ex: \\servidor\telefonia\ramais.json ou Z:\VoIP")
        edit_caminho.setObjectName("searchEdit")
        row_input.addWidget(edit_caminho)

        btn_procurar = QPushButton("📁 Procurar...")
        btn_procurar.setObjectName("btnNavDark")
        def _procurar():
            arq, _ = QFileDialog.getOpenFileName(dlg, "Selecionar Arquivo JSON de Ramais", "", "Arquivos JSON (*.json);;Todos (*.*)")
            if arq:
                edit_caminho.setText(arq)
            else:
                pasta = QFileDialog.getExistingDirectory(dlg, "Selecionar Pasta da Rede")
                if pasta:
                    edit_caminho.setText(pasta)
        btn_procurar.clicked.connect(_procurar)
        row_input.addWidget(btn_procurar)
        lay.addLayout(row_input)

        chk_auto = QCheckBox("Buscar e sincronizar o JSON automaticamente assim que iniciar")
        chk_auto.setChecked(auto_sync_atual)
        chk_auto.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 600;")
        lay.addWidget(chk_auto)

        row_acoes = QHBoxLayout()
        row_acoes.setSpacing(10)

        btn_sync_agora = QPushButton("🔄 Sincronizar Agora")
        btn_sync_agora.setObjectName("btnNavVerify")
        btn_sync_agora.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        btn_salvar = QPushButton("Salvar Configuração")
        btn_salvar.setObjectName("btnHeroNetwork")
        btn_salvar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("btnNavDark")
        btn_fechar.clicked.connect(dlg.reject)

        def _salvar_cfg():
            novo_caminho = edit_caminho.text().strip()
            cfg_dados = {
                "caminho_rede": novo_caminho,
                "auto_sync": chk_auto.isChecked(),
                "ultima_sincronizacao": datetime.now().isoformat(),
                "status": "configurado" if novo_caminho else "nao_configurado",
                "mensagem": "Caminho configurado com sucesso"
            }
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg_dados, f, indent=2, ensure_ascii=False)
            return novo_caminho

        def _exec_sync_agora():
            caminho = _salvar_cfg()
            if not caminho:
                QMessageBox.warning(dlg, "Aviso", "Por favor informe o caminho da pasta da rede antes de sincronizar.")
                return
            self._executar_sincronizacao_rede(caminho, silencioso=False, parent_dlg=dlg)

        def _exec_salvar_e_fechar():
            _salvar_cfg()
            QMessageBox.information(dlg, "Salvo", "Configurações da pasta da rede salvas com sucesso!")
            dlg.accept()

        btn_sync_agora.clicked.connect(_exec_sync_agora)
        btn_salvar.clicked.connect(_exec_salvar_e_fechar)

        row_acoes.addWidget(btn_sync_agora)
        row_acoes.addWidget(btn_salvar)
        row_acoes.addStretch()
        row_acoes.addWidget(btn_fechar)
        lay.addLayout(row_acoes)

        dlg.exec()

    def _sincronizar_rede_startup(self):
        """Busca o JSON assim que iniciar em uma pasta da rede se estiver configurado."""
        try:
            cfg_path = Path("data/network_config.json")
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                caminho = cfg.get("caminho_rede", "")
                if caminho and cfg.get("auto_sync", True):
                    self._executar_sincronizacao_rede(caminho, silencioso=True)
        except Exception as e:
            logger.warning("Falha ao sincronizar pasta da rede no startup: %s", e)

    def _executar_sincronizacao_rede(self, caminho_rede: str, silencioso: bool = False, parent_dlg=None):
        """Lê os ramais a partir do caminho da rede informado, atualiza o store local e recarrega a UI."""
        parent_ui = parent_dlg or self
        p = Path(caminho_rede.strip().strip('"').strip("'"))

        arquivo_json = None
        if p.is_file() and p.suffix.lower() == ".json":
            arquivo_json = p
        elif p.is_dir():
            candidatos = list(p.glob("*.json"))
            if candidatos:
                candidatos.sort(key=lambda f: (
                    0 if "ramais" in f.name.lower() or "haoc" in f.name.lower() else 1,
                    -f.stat().st_mtime
                ))
                arquivo_json = candidatos[0]

        if not arquivo_json or not arquivo_json.exists():
            msg = f"Nenhum arquivo JSON válido encontrado no caminho especificado:\n{caminho_rede}"
            logger.warning(msg)
            if not silencioso:
                QMessageBox.warning(parent_ui, "Falha na Sincronização", msg)
            return False

        try:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                dados = json.load(f)

            novos_ramais = []
            if isinstance(dados, dict):
                if "ramais" in dados and isinstance(dados["ramais"], list):
                    novos_ramais = dados["ramais"]
                else:
                    for nome_bloco, lista in dados.items():
                        if isinstance(lista, list):
                            for item in lista:
                                if isinstance(item, dict):
                                    novos_ramais.append({
                                        "descricao": item.get("Descrição") or item.get("descricao") or "Ramal VoIP",
                                        "bloco": nome_bloco,
                                        "setor": item.get("Setor") or item.get("setor") or "Geral",
                                        "ip": item.get("I.P") or item.get("ip") or "",
                                        "mac_cisco": item.get("I.P Cisco") or item.get("mac_cisco") or "",
                                        "modelo": item.get("Modelo") or item.get("modelo") or "Cisco CP-7841",
                                    })
            elif isinstance(dados, list):
                novos_ramais = dados

            if not novos_ramais:
                if not silencioso:
                    QMessageBox.warning(parent_ui, "Aviso", "O arquivo JSON encontrado não contém ramais reconhecidos.")
                return False

            import re
            lista_final = []
            id_seq = 1
            for item in novos_ramais:
                desc = item.get("descricao") or item.get("Descrição") or ""
                num = item.get("numero")
                if not num:
                    m = re.search(r"(\d{4})", desc)
                    num = m.group(1) if m else str(1000 + id_seq)

                ip = str(item.get("ip") or item.get("I.P") or "").strip()
                if ip.lower() in ["none", "null", "undefined"]:
                    ip = ""
                st = "ONLINE" if ip else "OFFLINE"

                lista_final.append({
                    "id": id_seq,
                    "numero": str(num),
                    "descricao": desc,
                    "bloco": item.get("bloco") or item.get("Bloco") or "Bloco Central",
                    "setor": item.get("setor") or item.get("Setor") or "Geral",
                    "ip": ip,
                    "mac_cisco": item.get("mac_cisco") or item.get("I.P Cisco") or "00:27:0D:00:00:00",
                    "modelo": item.get("modelo") or item.get("Modelo") or "Cisco CP-7841",
                    "status": st,
                    "ativo": True,
                    "latencia": 12 if st == "ONLINE" else None,
                    "ultima_verificacao": datetime.now().isoformat()
                })
                id_seq += 1

            store_path = Path("data/store.json")
            store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(store_path, "w", encoding="utf-8") as f:
                json.dump({"ramais": lista_final}, f, indent=2, ensure_ascii=False)

            cfg_path = Path("data/network_config.json")
            if cfg_path.exists():
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        c_dict = json.load(f)
                    c_dict["ultima_sincronizacao"] = datetime.now().isoformat()
                    c_dict["status"] = "sincronizado"
                    c_dict["mensagem"] = f"{len(lista_final)} ramais sincronizados de {arquivo_json.name}"
                    with open(cfg_path, "w", encoding="utf-8") as f:
                        json.dump(c_dict, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

            self._carregar_dados_interface()

            if not silencioso:
                QMessageBox.information(
                    parent_ui,
                    "Sincronização de Rede Concluída",
                    f"✓ Sincronizados com sucesso {len(lista_final)} ramais do arquivo:\n{arquivo_json.resolve()}"
                )
            return True
        except Exception as e:
            logger.error("Erro ao sincronizar JSON da rede: %s", e)
            if not silencioso:
                QMessageBox.critical(parent_ui, "Erro de Leitura", f"Falha ao ler o arquivo JSON:\n{e}")
            return False

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
        card = self.cartoes_map.get(ramal_id)
        status_txt = f"Ping ramal #{ramal_id}: {'ONLINE (' + str(round(latencia, 1)) + 'ms)' if sucesso else 'OFFLINE (' + erro + ')'}"
        self.lbl_sb_msg.setText(status_txt)
        if card:
            card.ramal_data["status"] = "ONLINE" if sucesso else "OFFLINE"
            card.ramal_data["latencia_ms"] = latencia if sucesso else None
            # Recarregar para reordenar dinamicamente caso o status tenha mudado
            self._carregar_dados_interface()

        # Exibir feedback no diálogo "Resultado do Ping" com contraste institucional
        if sucesso:
            QMessageBox.information(
                self,
                "Resultado do Ping",
                f"✅ Conexão estabelecida com sucesso!\nLatência: {latencia:.1f} ms"
            )
        else:
            QMessageBox.warning(
                self,
                "Resultado do Ping",
                f"❌ Falha na conexão com o ramal #{ramal_id}!\nMotivo: {erro or 'Inalcançável / Timeout'}"
            )
