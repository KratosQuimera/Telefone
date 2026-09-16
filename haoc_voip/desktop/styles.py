"""
Estilos e Temas Visuais (QSS) para a Aplicação Desktop PyQt6.
Paleta corporativa hospitalar de alto contraste, ergonômica e resistente a interferências de temas do OS.
"""

HOSPITAL_LIGHT_THEME = """
QMainWindow, QDialog {
    background-color: #f1f5f9;
    color: #0f172a;
    font-family: 'Segoe UI', Arial, sans-serif;
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

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #cbd5e1;
    padding: 6px;
    spacing: 8px;
}

QToolButton {
    background-color: transparent;
    color: #334155;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}

QToolButton:hover {
    background-color: #f1f5f9;
    border-color: #cbd5e1;
    color: #0284c7;
}

QToolButton:pressed {
    background-color: #e2e8f0;
}

QToolButton:disabled {
    color: #94a3b8;
}

QLineEdit, QComboBox, QSpinBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px 10px;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    min-height: 24px;
    color: #0f172a;
}

QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #0284c7;
}

QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #0369a1;
}

QPushButton:pressed {
    background-color: #075985;
}

QPushButton:disabled {
    background-color: #cbd5e1;
    color: #94a3b8;
}

QPushButton#btnSecondary {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
}

QPushButton#btnSecondary:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
}

QPushButton#btnSuccess {
    background-color: #16a34a;
    color: #ffffff;
}

QPushButton#btnSuccess:hover {
    background-color: #15803d;
}

QPushButton#btnDanger {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#btnDanger:hover {
    background-color: #b91c1c;
}

QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #cbd5e1;
    color: #475569;
    font-size: 12px;
}

QStatusBar QLabel {
    padding: 2px 8px;
}

QTableWidget, QTableView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    gridline-color: #f1f5f9;
    selection-background-color: #e0f2fe;
    selection-color: #0369a1;
    border-radius: 6px;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #cbd5e1;
    border-right: 1px solid #e2e8f0;
    font-weight: 600;
}

QScrollBar:vertical {
    background: #f1f5f9;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
"""

STATUS_COLORS = {
    "ONLINE": "#16a34a",     # Verde
    "OFFLINE": "#dc2626",    # Vermelho
}
