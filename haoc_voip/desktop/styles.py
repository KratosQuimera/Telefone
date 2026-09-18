"""
Estilos e Temas Visuais (QSS) para a Aplicação Desktop PyQt6.
Paleta corporativa hospitalar com suporte total ao TEMA ESCURO (NOC Dark Theme)
do Hospital Alemão Osvaldo Cruz VoIP Monitor Enterprise.
Garante paridade visual 100% fiel entre as versões Web e Desktop.
"""

HOSPITAL_DARK_THEME = """
QMainWindow, QDialog {
    background-color: #0a0e17;
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QWidget#centralWidget, QWidget#widgetConteudo {
    background-color: #0a0e17;
}

QScrollArea {
    border: none;
    background-color: #0a0e17;
}

QScrollArea > QWidget > QWidget {
    background-color: #0a0e17;
}

/* ========================================================================= */
/* BARRA SUPERIOR (NAVBAR DARK #0d131f)                                      */
/* ========================================================================= */
QFrame#topNavbar {
    background-color: #0d131f;
    border-bottom: 1px solid #1e293b;
    padding: 0px;
}

QPushButton#btnNavVerify {
    background-color: #059669;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 14px;
    border: none;
}
QPushButton#btnNavVerify:hover {
    background-color: #10b981;
}

QPushButton#btnNavDark {
    background-color: #161f30;
    color: #cbd5e1;
    font-weight: 600;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: 1px solid #334155;
}
QPushButton#btnNavDark:hover {
    background-color: #1f2d47;
    border-color: #475569;
    color: #ffffff;
}

QPushButton#btnNavNetwork {
    background-color: #162032;
    color: #7dd3fc;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 14px;
    border: 1px solid #0369a1;
}
QPushButton#btnNavNetwork:hover {
    background-color: #0c4a6e;
    color: #bae6fd;
}

QPushButton#btnNavLock {
    background-color: #161f30;
    color: #94a3b8;
    font-weight: 600;
    font-size: 12px;
    border-radius: 8px;
    padding: 5px 10px;
    border: 1px solid #334155;
}
QPushButton#btnNavLock:hover {
    background-color: #4c0519;
    border-color: #9f1239;
    color: #fda4af;
}

QPushButton#btnNavAdmin {
    background-color: #161f30;
    color: #facc15;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 14px;
    border: 1px solid #ca8a04;
}
QPushButton#btnNavAdmin:hover {
    background-color: #713f12;
    color: #fef08a;
}

/* ========================================================================= */
/* HERO BANNER (#0d131f -> #162032)                                          */
/* ========================================================================= */
QFrame#heroBanner {
    background-color: #0d131f;
    border: 1px solid #1e293b;
    border-radius: 14px;
}

QPushButton#btnHeroNetwork {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 16px;
    padding: 7px 16px;
    border: none;
}
QPushButton#btnHeroNetwork:hover {
    background-color: #0ea5e9;
}

/* ========================================================================= */
/* CARDS DE KPI (STATS BAR DARK)                                             */
/* ========================================================================= */
QFrame#kpiCard {
    background-color: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QFrame#kpiCard:hover {
    border-color: #334155;
}

/* ========================================================================= */
/* CONTAINER DE BUSCA E FILTROS (DARK)                                       */
/* ========================================================================= */
QFrame#filterCard {
    background-color: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
}

QLineEdit#searchEdit {
    background-color: #161f30;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 12px;
    color: #f8fafc;
}
QLineEdit#searchEdit:focus {
    border: 1.5px solid #10b981;
    background-color: #1a253a;
}

/* Pills de Status */
QPushButton#pillStatusAll {
    background-color: #161f30;
    color: #94a3b8;
    font-weight: 700;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 12px;
    border: 1px solid #334155;
}
QPushButton#pillStatusAllActive {
    background-color: #1e293b;
    color: #ffffff;
    font-weight: 800;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 12px;
    border: 1.5px solid #64748b;
}

QPushButton#pillStatusOnline {
    background-color: #161f30;
    color: #34d399;
    font-weight: 700;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 12px;
    border: 1px solid #064e3b;
}
QPushButton#pillStatusOnlineActive {
    background-color: #064e3b;
    color: #6ee7b7;
    font-weight: 800;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 12px;
    border: 1.5px solid #059669;
}

QPushButton#pillStatusOffline {
    background-color: #161f30;
    color: #fb7185;
    font-weight: 700;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 12px;
    border: 1px solid #881337;
}
QPushButton#pillStatusOfflineActive {
    background-color: #881337;
    color: #fda4af;
    font-weight: 800;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 12px;
    border: 1.5px solid #e11d48;
}

/* Pills de Blocos */
QPushButton#pillBloco {
    background-color: #161f30;
    color: #94a3b8;
    font-weight: 600;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 10px;
    border: 1px solid #334155;
}
QPushButton#pillBloco:hover {
    background-color: #1f2b3e;
    color: #f1f5f9;
}
QPushButton#pillBlocoActive {
    background-color: #059669;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    border-radius: 6px;
    padding: 5px 10px;
    border: none;
}

/* ========================================================================= */
/* BANNER DE ALERTA DE RAMAIS OFFLINE (PRIORIDADE NOC)                       */
/* ========================================================================= */
QFrame#noticeBanner {
    background-color: rgba(136, 19, 55, 0.4);
    border: 1px solid #be123c;
    border-radius: 10px;
}

/* ========================================================================= */
/* CARTÃO DE RAMAL COMPACTO (RAMAL CARD DARK)                                */
/* ========================================================================= */
QFrame#ramalCardOnline {
    background-color: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QFrame#ramalCardOnline:hover {
    border-color: #10b981;
    background-color: #131d2e;
}

QFrame#ramalCardOffline {
    background-color: #16101a;
    border: 1.5px solid #e11d48;
    border-radius: 12px;
}

QFrame#cardDetailBox {
    background-color: #0b0f19;
    border: 1px solid #1e293b;
    border-radius: 8px;
}

QPushButton#btnCardPing {
    background-color: #161f30;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
}
QPushButton#btnCardPing:hover {
    background-color: #064e3b;
    border-color: #059669;
    color: #34d399;
}

QPushButton#btnCardMenu {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: bold;
    padding: 0px 4px;
}
QPushButton#btnCardMenu:hover {
    background-color: #1e293b;
    color: #f1f5f9;
}

/* ========================================================================= */
/* STATUS BAR                                                                */
/* ========================================================================= */
QStatusBar {
    background-color: #0d131f;
    border-top: 1px solid #1e293b;
    color: #94a3b8;
    font-size: 11px;
}

/* ========================================================================= */
/* MENUS DE CONTEXTO (POPUP)                                                 */
/* ========================================================================= */
QMenu {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 4px 0px;
    color: #f1f5f9;
}
QMenu::item {
    padding: 6px 20px;
    font-size: 12px;
}
QMenu::item:selected {
    background-color: #1e293b;
    color: #34d399;
}

/* ========================================================================= */
/* SCROLLBAR MODERNA ESCURA                                                  */
/* ========================================================================= */
QScrollBar:vertical {
    background: #0a0e17;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar:horizontal {
    background: #0a0e17;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 24px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #475569;
}
"""

HOSPITAL_LIGHT_THEME = HOSPITAL_DARK_THEME

STATUS_COLORS = {
    "ONLINE": "#059669",
    "OFFLINE": "#e11d48",
}


def aplicar_tema_aplicacao(app):
    """
    Aplica paleta de cores Dark e estilos QSS ao QApplication.
    Hospital Alemão Osvaldo Cruz VoIP Monitor Enterprise NOC.
    """
    from PyQt6.QtGui import QPalette, QColor

    try:
        app.setStyle("Fusion")
    except Exception:
        pass

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0a0e17"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f1f5f9"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0d131f"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f1f5f9"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#161f30"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f1f5f9"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#f43f5e"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#059669"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#38bdf8"))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#0284c7"))

    app.setPalette(palette)
    app.setStyleSheet(HOSPITAL_DARK_THEME)
