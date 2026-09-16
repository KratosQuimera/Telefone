"""
Estilos e Temas Visuais (QSS) para a Aplicação Desktop PyQt6.
Paleta corporativa hospitalar de alto contraste, ergonômica e resistente a interferências de temas do OS.
Design idêntico ao painel NOC Web do HAOC VoIP Monitor Enterprise.
"""

HOSPITAL_LIGHT_THEME = """
QMainWindow, QDialog {
    background-color: #f1f5f9;
    color: #0f172a;
    font-family: 'Segoe UI', Arial, -apple-system, sans-serif;
    font-size: 13px;
}

QWidget#centralWidget, QWidget#widgetConteudo {
    background-color: #f1f5f9;
}

QScrollArea {
    border: none;
    background-color: #f1f5f9;
}

QScrollArea > QWidget > QWidget {
    background-color: #f1f5f9;
}

/* ========================================================================= */
/* BARRA SUPERIOR (HEADER MODERNO NOC)                                       */
/* ========================================================================= */
QFrame#topNavbar {
    background-color: #0f172a;
    border-bottom: 1px solid #1e293b;
    padding: 0px;
}

/* Botões do Top Navbar */
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
    background-color: #1e293b;
    color: #f8fafc;
    font-weight: 600;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: 1px solid #334155;
}
QPushButton#btnNavDark:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton#btnNavExe {
    background-color: #4f46e5;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 14px;
    border: none;
}
QPushButton#btnNavExe:hover {
    background-color: #6366f1;
}

QPushButton#btnNavAdmin {
    background-color: #1e293b;
    color: #eab308;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 14px;
    border: 1px solid #ca8a04;
}
QPushButton#btnNavAdmin:hover {
    background-color: #854d0e;
    color: #fef08a;
}

QPushButton#btnNavAdminLogged {
    background-color: #064e3b;
    color: #34d399;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 14px;
    border: 1px solid #059669;
}
QPushButton#btnNavAdminLogged:hover {
    background-color: #047857;
    color: #ffffff;
}

/* ========================================================================= */
/* HERO BANNER                                                               */
/* ========================================================================= */
QFrame#heroBanner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:0.6 #1e293b, stop:1 #1e1b4b);
    border: 1px solid #334155;
    border-radius: 16px;
}

QPushButton#btnHeroExe {
    background-color: #059669;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
}
QPushButton#btnHeroExe:hover {
    background-color: #10b981;
}

/* ========================================================================= */
/* CARDS DE KPI (STATS BAR)                                                  */
/* ========================================================================= */
QFrame#kpiCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}
QFrame#kpiCard:hover {
    border-color: #cbd5e1;
}

/* ========================================================================= */
/* CONTAINER DE BUSCA E FILTROS                                              */
/* ========================================================================= */
QFrame#filterCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}

QLineEdit#searchEdit {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 12px;
    color: #0f172a;
}
QLineEdit#searchEdit:focus {
    border: 1.5px solid #059669;
    background-color: #ffffff;
}

/* Pills de Status */
QPushButton#pillStatusAll {
    background-color: #ffffff;
    color: #0f172a;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: 1px solid #cbd5e1;
}
QPushButton#pillStatusAllActive {
    background-color: #0f172a;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: none;
}

QPushButton#pillStatusOnline {
    background-color: #f8fafc;
    color: #16a34a;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: 1px solid #bbf7d0;
}
QPushButton#pillStatusOnlineActive {
    background-color: #16a34a;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: none;
}

QPushButton#pillStatusOffline {
    background-color: #f8fafc;
    color: #dc2626;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: 1px solid #fecaca;
}
QPushButton#pillStatusOfflineActive {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: none;
}

/* Pills de Blocos */
QPushButton#pillBloco {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 600;
    font-size: 11px;
    border-radius: 8px;
    padding: 5px 10px;
    border: 1px solid transparent;
}
QPushButton#pillBloco:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}
QPushButton#pillBlocoActive {
    background-color: #0f172a;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    border-radius: 8px;
    padding: 5px 10px;
    border: none;
}

/* ========================================================================= */
/* CARTÃO DE RAMAL (RAMAL CARD)                                              */
/* ========================================================================= */
QFrame#ramalCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}
QFrame#ramalCard:hover {
    border: 1.5px solid #10b981;
}

QFrame#ramalCardOnline {
    background-color: #ffffff;
    border: 1px solid #bbf7d0;
    border-radius: 14px;
}
QFrame#ramalCardOnline:hover {
    border: 1.5px solid #10b981;
}

QFrame#ramalCardOffline {
    background-color: #ffffff;
    border: 1px solid #fecaca;
    border-radius: 14px;
}
QFrame#ramalCardOffline:hover {
    border: 1.5px solid #ef4444;
}

QFrame#cardDetailBox {
    background-color: #f8fafc;
    border: 1px solid #f1f5f9;
    border-radius: 8px;
}

QPushButton#btnCardPing {
    background-color: #f8fafc;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
}
QPushButton#btnCardPing:hover {
    background-color: #ecfdf5;
    border-color: #10b981;
    color: #047857;
}

QPushButton#btnCardMenu {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    font-weight: bold;
    padding: 0px 4px;
}
QPushButton#btnCardMenu:hover {
    background-color: #f1f5f9;
    color: #334155;
}

/* ========================================================================= */
/* STATUS BAR                                                                */
/* ========================================================================= */
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #cbd5e1;
    color: #475569;
    font-size: 12px;
}

QScrollBar:vertical {
    background: #f1f5f9;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
"""

STATUS_COLORS = {
    "ONLINE": "#16a34a",
    "OFFLINE": "#dc2626",
}
