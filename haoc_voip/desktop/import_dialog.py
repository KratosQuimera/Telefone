"""
Diálogo de Importação e Comparação Visual de JSON em PyQt6.
Diff estruturado com validação de formato e aplicação seletiva.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import json

from haoc_voip.core.importer import JSONImporter, exportar_para_json_legado
from haoc_voip.core.database import db
from haoc_voip.core.models import Ramal


class ImportDialog(QDialog):
    """Diálogo para sincronização entre o arquivo JSON legado e o SQLite."""

    def __init__(self, usuario_atual=None, parent=None):
        super().__init__(parent)
        self.usuario_atual = usuario_atual
        self.setWindowTitle("HAOC VoIP Monitor - Importação e Diff JSON")
        self.resize(920, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.resultado_diff: dict | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Header com seleção de arquivo
        top_bar = QHBoxLayout()
        self.lbl_arquivo = QLabel("Nenhum arquivo JSON selecionado.")
        self.lbl_arquivo.setStyleSheet("font-weight: 700; color: #334155; font-size: 12px;")
        top_bar.addWidget(self.lbl_arquivo)
        top_bar.addStretch()

        btn_modelo = QPushButton("📄 Modelo JSON Oficial")
        btn_modelo.setObjectName("btnSecondary")
        btn_modelo.setToolTip("Salvar modelo oficial de JSON com a estrutura por Blocos")
        btn_modelo.clicked.connect(self._salvar_modelo_json)
        top_bar.addWidget(btn_modelo)

        btn_exportar = QPushButton("💾 Exportar Base (.json)")
        btn_exportar.setObjectName("btnSecondary")
        btn_exportar.setToolTip("Exportar os ramais cadastrados no formato oficial de Blocos")
        btn_exportar.clicked.connect(self._exportar_base_json)
        top_bar.addWidget(btn_exportar)

        btn_selecionar = QPushButton("📂 Selecionar Arquivo JSON...")
        btn_selecionar.setObjectName("btnPrimary")
        btn_selecionar.clicked.connect(self._selecionar_arquivo)
        top_bar.addWidget(btn_selecionar)

        layout.addLayout(top_bar)

        # Resumo das diferenças
        self.lbl_resumo = QLabel("Aguardando carregamento de arquivo.")
        self.lbl_resumo.setStyleSheet("font-size: 12px; color: #0f172a; padding: 4px 0; font-weight: 600;")
        layout.addWidget(self.lbl_resumo)

        # Tabela de Diff
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels([
            "Aplicar", "Tipo", "Descrição", "Bloco", "IP", "MAC Cisco", "Diferenças Detectadas"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        layout.addWidget(self.tabela)

        # Barra inferior
        bottom_bar = QHBoxLayout()
        self.chk_remover_ausentes = QCheckBox("Desativar no banco os ramais ausentes no JSON")
        bottom_bar.addWidget(self.chk_remover_ausentes)

        bottom_bar.addStretch()

        perfil_u = getattr(self.usuario_atual, "perfil", None) or (self.usuario_atual.get("perfil") if isinstance(self.usuario_atual, dict) else None)
        if perfil_u in ["ADMINISTRADOR", "ANALISTA"]:
            self.btn_aplicar = QPushButton("🚀 Aplicar Alterações Selecionadas")
            self.btn_aplicar.setObjectName("btnPrimary")
            self.btn_aplicar.setEnabled(False)
            self.btn_aplicar.clicked.connect(self._aplicar_diff)
            bottom_bar.addWidget(self.btn_aplicar)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("btnSecondary")
        btn_fechar.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_fechar)

        layout.addLayout(bottom_bar)

    def _selecionar_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar JSON de Ramais", "", "Arquivos JSON (*.json)"
        )
        if not caminho:
            return

        self.lbl_arquivo.setText(f"Arquivo: {caminho}")

        try:
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo_str = f.read()

            self._conteudo_json = conteudo_str
            self._importer = JSONImporter(conteudo_str)
            self.resultado_diff = self._importer.validar_e_analisar()
            self._renderizar_diff()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Ler JSON", f"Falha ao processar arquivo:\n{str(e)}")

    def _renderizar_diff(self):
        if not self.resultado_diff:
            return

        novos = self.resultado_diff.get("novos", [])
        alterados = self.resultado_diff.get("alterados", [])
        removidos = self.resultado_diff.get("removidos", [])
        estatisticas = self.resultado_diff.get("estatisticas", {})

        self.lbl_resumo.setText(
            f"Total no JSON: {estatisticas.get('total_no_arquivo', 0)} | "
            f"Novos: {len(novos)} | "
            f"Com Alterações: {len(alterados)} | "
            f"Removidos/Ausentes: {len(removidos)}"
        )

        # Agrupar itens com formato padronizado para a tabela
        itens_grid = []
        for n in novos:
            itens_grid.append({
                "tipo": "NOVO",
                "dados": n,
                "descricao": n.get("descricao", ""),
                "bloco": n.get("bloco", ""),
                "ip": n.get("ip", ""),
                "mac": n.get("mac_cisco", ""),
                "detalhes": "Novo ramal a ser inserido na base",
            })
        for a in alterados:
            mud = a.get("mudancas", {})
            mud_str = "; ".join([f"{k}: {v['anterior']} ➔ {v['novo']}" for k, v in mud.items()])
            itens_grid.append({
                "tipo": "ALTERADO",
                "dados": a,
                "descricao": a.get("descricao", ""),
                "bloco": a.get("bloco", ""),
                "ip": a.get("ip", ""),
                "mac": a.get("mac_cisco", ""),
                "detalhes": mud_str or "Propriedades modificadas",
            })
        for r in removidos:
            itens_grid.append({
                "tipo": "REMOVIDO",
                "dados": r,
                "descricao": r.get("descricao", ""),
                "bloco": r.get("bloco", ""),
                "ip": r.get("ip", ""),
                "mac": r.get("mac_cisco", ""),
                "detalhes": "Presente no banco mas ausente no arquivo JSON",
            })

        self._itens_grid = itens_grid
        self.tabela.setRowCount(len(itens_grid))

        for row_idx, item in enumerate(itens_grid):
            tipo = item["tipo"]
            # Checkbox na coluna 0
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Checked if tipo in ["NOVO", "ALTERADO"] else Qt.CheckState.Unchecked)
            self.tabela.setItem(row_idx, 0, chk_item)

            tipo_item = QTableWidgetItem(tipo)
            if tipo == "NOVO":
                tipo_item.setForeground(QColor("#16a34a"))
            elif tipo == "ALTERADO":
                tipo_item.setForeground(QColor("#0284c7"))
            elif tipo == "REMOVIDO":
                tipo_item.setForeground(QColor("#dc2626"))
            self.tabela.setItem(row_idx, 1, tipo_item)

            self.tabela.setItem(row_idx, 2, QTableWidgetItem(item["descricao"]))
            self.tabela.setItem(row_idx, 3, QTableWidgetItem(item["bloco"]))
            self.tabela.setItem(row_idx, 4, QTableWidgetItem(item["ip"] or "-"))
            self.tabela.setItem(row_idx, 5, QTableWidgetItem(item["mac"] or "-"))
            self.tabela.setItem(row_idx, 6, QTableWidgetItem(item["detalhes"]))

        if hasattr(self, "btn_aplicar"):
            self.btn_aplicar.setEnabled(len(itens_grid) > 0)

    def _aplicar_diff(self):
        if not hasattr(self, "_importer") or not hasattr(self, "_itens_grid"):
            return

        # Coletar itens marcados
        selecionados = []
        for row in range(self.tabela.rowCount()):
            chk = self.tabela.item(row, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                selecionados.append(self._itens_grid[row]["dados"])

        if not selecionados and not self.chk_remover_ausentes.isChecked():
            QMessageBox.warning(self, "Aviso", "Nenhuma alteração foi marcada para aplicação.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmar Aplicação",
            f"Deseja aplicar as {len(selecionados)} alterações selecionadas na base de dados?\n"
            f"Um backup de segurança do SQLite será criado automaticamente antes da gravação.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            uid = getattr(self.usuario_atual, "id", None) or (self.usuario_atual.get("id") if isinstance(self.usuario_atual, dict) else None)
            res = self._importer.aplicar_alteracoes(
                itens_selecionados=selecionados,
                remover_ausentes=self.chk_remover_ausentes.isChecked(),
                usuario_id=uid,
            )
            msg = f"Sincronização concluída com sucesso!\n\n• Inseridos: {res.get('inseridos', 0)}\n• Atualizados: {res.get('atualizados', 0)}\n• Desativados: {res.get('desativados', 0)}"
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro na Aplicação", f"Falha ao sincronizar base: {str(exc)}")

    def _salvar_modelo_json(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Modelo JSON Oficial por Blocos",
            "modelo_ramais_haoc.json",
            "Arquivos JSON (*.json)"
        )
        if not caminho:
            return

        modelo = {
            "Bloco A": [
                {
                    "Modelo": "Cisco Unified Client Services Framework",
                    "I.P Cisco": "CSF18982",
                    "Descrição": "JABBER - Recp_Bl.A - Ouvidoria - 6452",
                    "I.P": "None"
                },
                {
                    "Modelo": "Cisco 7841",
                    "I.P Cisco": "SEP2C86D276454B",
                    "Descrição": "Matriz - 1A Bl.A - Juridico - 0351",
                    "I.P": "10.192.58.24"
                }
            ],
            "Bloco B": [
                {
                    "Modelo": "Cisco 7841",
                    "I.P Cisco": "SEP2C86D2764624",
                    "Descrição": "Matriz - 10A_Bl.B - 10B Quarto 1000 - 1000",
                    "I.P": "10.193.28.25"
                },
                {
                    "Modelo": "Cisco 7841",
                    "I.P Cisco": "SEP2C3ECF86C880",
                    "Descrição": "Matriz - 10A_Bl.B - 10B Quarto 1001 - 1001",
                    "I.P": "10.193.28.130"
                }
            ],
            "Bloco E": [
                {
                    "Modelo": "Cisco 7841",
                    "I.P Cisco": "SEP2C3ECF87F9C5",
                    "Descrição": "Matriz - 10A_Bl.E - 10E Quarto 1016 - 1016",
                    "I.P": "10.195.28.91"
                },
                {
                    "Modelo": "Cisco 7841",
                    "I.P Cisco": "SEP2C3ECF86C4AB",
                    "Descrição": "Matriz - 10A_Bl.E - 10E Quarto 1017 - 1017",
                    "I.P": "10.195.28.165"
                }
            ]
        }

        try:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(modelo, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Sucesso", f"Modelo oficial salvo com sucesso em:\n{caminho}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o modelo:\n{str(e)}")

    def _exportar_base_json(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Base de Ramais em Formato por Blocos",
            "ramais_haoc_exportados.json",
            "Arquivos JSON (*.json)"
        )
        if not caminho:
            return

        try:
            dados = exportar_para_json_legado()
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            total = sum(len(v) for v in dados.values())
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Base exportada com sucesso!\n\n• Blocos: {len(dados)}\n• Total de Ramais: {total}\n• Arquivo: {caminho}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Falha ao exportar base:\n{str(e)}")
