"""
Diálogo de Histórico e Gestão de Incidentes em PyQt6.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QInputDialog,
    QFileDialog,
)
from PyQt6.QtCore import Qt
import csv
from datetime import datetime

from haoc_voip.core.models import Incidente, Ramal, Bloco
from haoc_voip.core.database import db
from haoc_voip.core.audit import registrar_auditoria


class IncidentesDialog(QDialog):
    """Visualização e anotação de ocorrências e indisponibilidades."""

    def __init__(self, usuario_atual=None, parent=None):
        super().__init__(parent)
        self.usuario_atual = usuario_atual
        self.setWindowTitle("HAOC VoIP Monitor - Histórico de Incidentes")
        self.resize(850, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()
        self._carregar_incidentes()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar superior com filtros
        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("Bloco:"))
        self.cb_bloco = QComboBox()
        self.cb_bloco.addItem("Todos os Blocos", "")
        top_bar.addWidget(self.cb_bloco)

        top_bar.addWidget(QLabel("Status:"))
        self.cb_status = QComboBox()
        self.cb_status.addItem("Todos", "")
        self.cb_status.addItem("Apenas Quedas Abertas", "aberto")
        self.cb_status.addItem("Resolvidos", "encerrado")
        top_bar.addWidget(self.cb_status)

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setObjectName("btnPrimary")
        btn_filtrar.clicked.connect(self._carregar_incidentes)
        top_bar.addWidget(btn_filtrar)

        top_bar.addStretch()

        # Botão exportar
        btn_csv = QPushButton("Exportar CSV")
        btn_csv.setObjectName("btnSecondary")
        btn_csv.clicked.connect(self._exportar_csv)
        top_bar.addWidget(btn_csv)

        layout.addLayout(top_bar)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Ramal", "Bloco", "Início Queda", "Retorno", "Duração", "Status", "Causa / Laudo"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        layout.addWidget(self.tabela)

        # Ações inferiores
        bottom_bar = QHBoxLayout()
        self.lbl_total = QLabel("Total de ocorrências: 0")
        self.lbl_total.setStyleSheet("color: #475569; font-size: 12px; font-weight: 600;")
        bottom_bar.addWidget(self.lbl_total)
        bottom_bar.addStretch()

        perfil_u = getattr(self.usuario_atual, "perfil", None) or (self.usuario_atual.get("perfil") if isinstance(self.usuario_atual, dict) else None)
        if perfil_u in ["ADMINISTRADOR", "ANALISTA"]:
            btn_anotar = QPushButton("Anotar Causa no Incidente Selecionado")
            btn_anotar.setObjectName("btnPrimary")
            btn_anotar.clicked.connect(self._anotar_incidente)
            bottom_bar.addWidget(btn_anotar)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("btnSecondary")
        btn_fechar.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_fechar)

        layout.addLayout(bottom_bar)

        # Carregar blocos no combo
        with db.session_scope() as session:
            blocos = session.query(Bloco).filter(Bloco.ativo == True).order_by(Bloco.nome).all()
            for b in blocos:
                self.cb_bloco.addItem(b.nome, b.nome)

    def _carregar_incidentes(self):
        filtro_bloco = self.cb_bloco.currentData()
        filtro_status = self.cb_status.currentData()

        with db.session_scope() as session:
            q = session.query(Incidente, Ramal).join(Ramal, Incidente.ramal_id == Ramal.id)
            if filtro_bloco:
                q = q.filter(Ramal.bloco == filtro_bloco)
            if filtro_status == "aberto":
                q = q.filter(Incidente.aberto == True)
            elif filtro_status == "encerrado":
                q = q.filter(Incidente.aberto == False)

            registros = q.order_by(Incidente.id.desc()).limit(200).all()

            self.tabela.setRowCount(len(registros))
            for row_idx, (inc, r) in enumerate(registros):
                self.tabela.setItem(row_idx, 0, QTableWidgetItem(str(inc.id)))
                self.tabela.setItem(row_idx, 1, QTableWidgetItem(r.descricao))
                self.tabela.setItem(row_idx, 2, QTableWidgetItem(r.bloco))
                
                ini_str = inc.iniciado_em.strftime("%d/%m/%Y %H:%M:%S") if inc.iniciado_em else "-"
                fim_str = inc.encerrado_em.strftime("%d/%m/%Y %H:%M:%S") if inc.encerrado_em else "EM QUEDA"
                
                self.tabela.setItem(row_idx, 3, QTableWidgetItem(ini_str))
                self.tabela.setItem(row_idx, 4, QTableWidgetItem(fim_str))
                self.tabela.setItem(row_idx, 5, QTableWidgetItem(inc.duracao_formatada))
                
                st_item = QTableWidgetItem("EM QUEDA" if inc.aberto else "RESOLVIDO")
                if inc.aberto:
                    st_item.setForeground(Qt.GlobalColor.red)
                else:
                    st_item.setForeground(Qt.GlobalColor.darkGreen)
                self.tabela.setItem(row_idx, 6, st_item)

                causa_desc = inc.causa or ""
                if inc.observacao:
                    causa_desc += f" - {inc.observacao}"
                self.tabela.setItem(row_idx, 7, QTableWidgetItem(causa_desc or "-"))

            self.lbl_total.setText(f"Exibindo {len(registros)} ocorrências")

    def _anotar_incidente(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um incidente na tabela.")
            return

        inc_id = int(self.tabela.item(row, 0).text())
        obs_atual = self.tabela.item(row, 7).text()

        nova_obs, ok = QInputDialog.getText(
            self, "Anotação do Analista", "Causa apurada e observação da equipe:", text=obs_atual
        )
        if ok and nova_obs:
            with db.session_scope() as session:
                inc = session.query(Incidente).filter(Incidente.id == inc_id).first()
                if inc:
                    inc.observacao = nova_obs
                    inc.causa = "Análise registrada pelo analista"
            
            registrar_auditoria(
                acao="ANOTAR_INCIDENTE_DESKTOP",
                entidade="incidente",
                entidade_id=inc_id,
                detalhes={"observacao": nova_obs},
                usuario_id=self.usuario_atual.id if self.usuario_atual else None,
                ip_origem="desktop_client",
            )
            self._carregar_incidentes()

    def _exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório de Incidentes", "incidentes_haoc.csv", "CSV (*.csv)"
        )
        if not caminho:
            return

        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["ID", "Ramal", "Bloco", "Início", "Retorno", "Duração", "Status", "Causa / Laudo"])
            for row in range(self.tabela.rowCount()):
                linha = [self.tabela.item(row, col).text() for col in range(self.tabela.columnCount())]
                writer.writerow(linha)

        QMessageBox.information(self, "Sucesso", f"Relatório exportado com sucesso para:\n{caminho}")
