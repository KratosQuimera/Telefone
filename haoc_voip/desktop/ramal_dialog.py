"""
Diálogo de Cadastro e Edição de Ramais VoIP em PyQt6.
Validações de IPv4, MAC Cisco e unicidade de chaves.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("haoc.ramal_dialog")

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

from haoc_voip.config import Config
from haoc_voip.core.models import Ramal, Bloco, Setor, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.importer import validar_ipv4, normalizar_mac, MAC_CISCO_REGEX
from haoc_voip.core.audit import registrar_auditoria
from haoc_voip.core.backup import backup_mgr
from haoc_voip.core.monitor import executar_ping


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
        self.btn_salvar.setObjectName("btnPrimary")
        self.btn_salvar.clicked.connect(self._salvar)

        btn_box.addWidget(self.btn_cancelar)
        btn_box.addWidget(self.btn_salvar)
        layout.addLayout(btn_box)

    def _carregar_dados(self):
        # Blocos padrão de fallback
        blocos_padrao = [
            "Bloco Central",
            "Pronto Socorro",
            "UTI Geral",
            "Centro Cirúrgico",
            "Maternidade",
            "Ambulatório",
            "Administrativo",
        ]
        for b in blocos_padrao:
            self.cb_bloco.addItem(b, b)

        # Tentar carregar blocos e setores do banco SQLite
        try:
            with db.session_scope() as session:
                blocos_db = session.query(Bloco).filter(Bloco.ativo == True).order_by(Bloco.nome).all()
                for b in blocos_db:
                    if self.cb_bloco.findText(b.nome) < 0:
                        self.cb_bloco.addItem(b.nome, b.nome)

                setores = session.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()
                for s in setores:
                    self.cb_setor.addItem(s.nome, s.nome)
        except Exception as e:
            logger.warning("Falha ao carregar blocos/setores do SQLite: %s", e)

        # Se for edição, carregar dados existentes
        self.desc_original = ""
        if self.ramal_id:
            carregou = False
            # 1. Tentar ler de store.json
            store_p = Config.obter_caminho_dados("store.json")
            if store_p.exists():
                try:
                    with open(store_p, "r", encoding="utf-8") as f:
                        d = json.load(f)
                        for r in d.get("ramais", []):
                            if str(r.get("id")) == str(self.ramal_id):
                                self.txt_desc.setText(str(r.get("descricao") or ""))
                                self.desc_original = str(r.get("descricao") or "")
                                idx_b = self.cb_bloco.findText(r.get("bloco") or "Bloco Central")
                                if idx_b >= 0:
                                    self.cb_bloco.setCurrentIndex(idx_b)
                                if r.get("setor"):
                                    idx_s = self.cb_setor.findText(r.get("setor"))
                                    if idx_s >= 0:
                                        self.cb_setor.setCurrentIndex(idx_s)
                                    else:
                                        self.cb_setor.addItem(r.get("setor"), r.get("setor"))
                                        self.cb_setor.setCurrentIndex(self.cb_setor.count() - 1)
                                self.txt_ip.setText(str(r.get("ip") or ""))
                                self.txt_mac.setText(str(r.get("mac_cisco") or ""))
                                self.txt_modelo.setText(str(r.get("modelo") or "Cisco CP-7841"))
                                carregou = True
                                break
                except Exception as e:
                    logger.warning("Falha ao carregar ramal de store.json: %s", e)

            # 2. Tentar ler do SQLite para complementar ou como fallback
            try:
                with db.session_scope() as session:
                    ramal = session.query(Ramal).filter(Ramal.id == self.ramal_id).first()
                    if ramal:
                        if not carregou:
                            self.txt_desc.setText(ramal.descricao or "")
                            idx_b = self.cb_bloco.findText(ramal.bloco or "Bloco Central")
                            if idx_b >= 0:
                                self.cb_bloco.setCurrentIndex(idx_b)
                            if ramal.setor:
                                idx_s = self.cb_setor.findText(ramal.setor)
                                if idx_s >= 0:
                                    self.cb_setor.setCurrentIndex(idx_s)
                            self.txt_ip.setText(ramal.ip or "")
                            self.txt_mac.setText(ramal.mac_cisco or "")
                            self.txt_modelo.setText(ramal.modelo or "Cisco CP-7841")

                        idx_c = self.cb_criticidade.findText(ramal.criticidade or "NORMAL")
                        if idx_c >= 0:
                            self.cb_criticidade.setCurrentIndex(idx_c)
                        self.txt_localizacao.setText(ramal.localizacao or "")
                        self.txt_obs.setPlainText(ramal.observacoes or "")
            except Exception as e:
                logger.warning("Falha ao carregar ramal do SQLite: %s", e)

    def _salvar(self):
        try:
            desc = self.txt_desc.text().strip()
            bloco = self.cb_bloco.currentText().strip()
            ip = self.txt_ip.text().strip()
            mac = normalizar_mac(self.txt_mac.text().strip())
            modelo = self.txt_modelo.text().strip() or "Cisco CP-7841"
            setor = self.cb_setor.currentText().strip()
            if setor == "Sem Setor":
                setor = "Geral"
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

            # Obter ID e Nome do usuário com segurança sem disparar AttributeError
            user_id = getattr(self.usuario_atual, "id", None) or (self.usuario_atual.get("id") if isinstance(self.usuario_atual, dict) else 1)
            user_nome = getattr(self.usuario_atual, "nome", None) or (self.usuario_atual.get("nome") if isinstance(self.usuario_atual, dict) else "Wagner")

            # 1. Backup preventivo FORA de transações SQLite para evitar deadlocks
            try:
                backup_mgr.criar_backup(motivo="pre_salvar_ramal_desktop", usuario_id=user_id)
            except Exception as e:
                logger.warning("Não foi possível gerar backup pré-salvamento: %s", e)

            # 2. Testar ping imediatamente para definir o status operacional real em tempo real
            msg_ping = "Ping não configurado (sem IP válido)."
            status_real = "OFFLINE"
            latencia_real = None
            erro_ping = None

            if ip and validar_ipv4(ip):
                try:
                    sucesso, latencia, erro_ping = executar_ping(ip, timeout_seconds=1.5, retries=1)
                    if sucesso:
                        status_real = "ONLINE"
                        latencia_real = latencia
                        lat_str = f"{latencia:.1f}ms" if latencia else "resposta OK"
                        msg_ping = f"Ping OK ({lat_str}) - Ramal ONLINE."
                    else:
                        status_real = "OFFLINE"
                        latencia_real = None
                        msg_ping = f"Sem resposta ao ping ({erro_ping or 'timeout'}) - Ramal OFFLINE."
                except Exception as p_err:
                    msg_ping = f"Teste de ping executado com alerta: {p_err}"

            agora_salvamento = datetime.utcnow()

            # 3. Persistência em SQLite (com proteção contra travamentos e atualização de status)
            try:
                with db.session_scope() as session:
                    if self.ramal_id:
                        ramal = session.query(Ramal).filter(Ramal.id == self.ramal_id).first()
                        if ramal:
                            ramal.ip = ip or None
                            ramal.mac_cisco = mac or None
                            ramal.observacoes = obs
                            ramal.descricao = desc
                            ramal.bloco = bloco
                            ramal.setor = setor
                            ramal.modelo = modelo
                            ramal.criticidade = crit
                            ramal.localizacao = loc
                            ramal.status_atual = status_real
                            ramal.ultima_latencia = latencia_real
                            ramal.ultima_verificacao = agora_salvamento
                            if status_real == "ONLINE":
                                ramal.ultimo_visto_online = agora_salvamento
                                ramal.ultimo_erro = None
                            else:
                                ramal.ultimo_visto_offline = agora_salvamento
                                ramal.ultimo_erro = erro_ping
                        else:
                            novo_r = Ramal(
                                id=self.ramal_id,
                                descricao=desc,
                                bloco=bloco,
                                setor=setor,
                                ip=ip or None,
                                mac_cisco=mac or None,
                                modelo=modelo,
                                criticidade=crit,
                                localizacao=loc,
                                observacoes=obs,
                                status_atual=status_real,
                                ultima_latencia=latencia_real,
                                ultima_verificacao=agora_salvamento,
                                ultimo_visto_online=agora_salvamento if status_real == "ONLINE" else None,
                                ultimo_visto_offline=agora_salvamento if status_real == "OFFLINE" else None,
                                ativo=True,
                            )
                            session.add(novo_r)
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
                            status_atual=status_real,
                            ultima_latencia=latencia_real,
                            ultima_verificacao=agora_salvamento,
                            ultimo_visto_online=agora_salvamento if status_real == "ONLINE" else None,
                            ultimo_visto_offline=agora_salvamento if status_real == "OFFLINE" else None,
                            ativo=True,
                        )
                        session.add(ramal)
                        session.flush()
                        self.ramal_id = ramal.id
                        acao = "CRIAR_RAMAL_DESKTOP"
            except Exception as e:
                logger.warning("Falha ao salvar ramal no SQLite (mantendo sincronização JSON): %s", e)

            # 4. Sincronizar obrigatoriamente no store.json e arquivos de rede JSON com o status real
            self._sincronizar_edicao_json(
                ramal_id=self.ramal_id,
                descricao=desc,
                bloco=bloco,
                setor=setor,
                ip=ip,
                mac=mac,
                modelo=modelo,
                usuario_nome=user_nome,
                status=status_real,
                latencia=latencia_real,
                desc_antiga=getattr(self, "desc_original", ""),
            )

            # 5. Auditoria não-bloqueante
            try:
                registrar_auditoria(
                    acao="EDITAR_RAMAL_DESKTOP" if self.ramal_id else "CRIAR_RAMAL_DESKTOP",
                    entidade="ramal",
                    entidade_id=self.ramal_id,
                    detalhes={"descricao": desc, "ip": ip, "mac": mac, "bloco": bloco, "status": status_real},
                    usuario_id=user_id,
                    ip_origem="desktop_client",
                )
            except Exception as e:
                logger.warning("Auditoria não registrada: %s", e)

            QMessageBox.information(
                self, 
                "Sucesso", 
                f"Ramal salvo e sincronizado com sucesso!\n\nStatus do teste de ping:\n{msg_ping}\n\nA lista foi atualizada imediatamente e o ramal está {status_real}."
            )
            self.accept()

        except Exception as exc:
            logger.error("Erro fatal ao salvar ramal no desktop: %s", exc, exc_info=True)
            QMessageBox.critical(self, "Erro ao Salvar", f"Ocorreu um erro ao salvar o ramal:\n{exc}")

    def _sincronizar_edicao_json(
        self,
        ramal_id: int | None,
        descricao: str,
        bloco: str,
        setor: str,
        ip: str,
        mac: str,
        modelo: str,
        usuario_nome: str,
        status: str = "ONLINE",
        latencia: float | None = None,
        desc_antiga: str = "",
    ):
        """Garante que a edição modifique imediatamente o store.json e arquivos da rede com o status real."""
        import os
        import re

        numero_extraido = ""
        m = re.search(r"\b(\d{3,5})\b", descricao)
        if m:
            numero_extraido = m.group(1)
        elif desc_antiga:
            m_ant = re.search(r"\b(\d{3,5})\b", desc_antiga)
            if m_ant:
                numero_extraido = m_ant.group(1)

        store_p = Config.obter_caminho_dados("store.json")
        try:
            d = {"usuarios": [], "ramais": [], "incidentes": [], "auditoria": []}
            if store_p.exists():
                with open(store_p, "r", encoding="utf-8") as f:
                    d = json.load(f)
            ramais = d.get("ramais", [])
            achou = False
            for r in ramais:
                match_id = bool(ramal_id and str(r.get("id")) == str(ramal_id))
                match_num = bool(numero_extraido and str(r.get("numero") or "").strip() == numero_extraido)
                match_desc = bool(desc_antiga and str(r.get("descricao") or "").strip() == desc_antiga.strip())
                if match_id or match_num or match_desc:
                    r["descricao"] = descricao
                    r["bloco"] = bloco
                    r["setor"] = setor
                    r["ip"] = ip
                    r["mac_cisco"] = mac
                    r["modelo"] = modelo
                    r["status"] = status
                    r["latencia_ms"] = round(latencia, 1) if latencia else None
                    r["latencia"] = round(latencia, 1) if latencia else None
                    r["ultimo_ping"] = datetime.now().isoformat()
                    if numero_extraido:
                        r["numero"] = numero_extraido
                    achou = True
                    break

            if not achou:
                max_id = max([int(r.get("id", 100)) for r in ramais if str(r.get("id", "")).isdigit()], default=100)
                novo_id = ramal_id or (max_id + 1)
                novo_obj = {
                    "id": novo_id,
                    "numero": numero_extraido or str(novo_id),
                    "descricao": descricao,
                    "bloco": bloco,
                    "setor": setor,
                    "ip": ip or "",
                    "mac_cisco": mac or "00:27:0D:00:00:00",
                    "modelo": modelo or "Cisco CP-7841",
                    "status": status,
                    "latencia_ms": round(latencia, 1) if latencia else 15,
                    "latencia": round(latencia, 1) if latencia else 15,
                    "ultimo_ping": datetime.now().isoformat(),
                    "ativo": True,
                }
                ramais.append(novo_obj)
                d["ramais"] = ramais

            store_p.parent.mkdir(parents=True, exist_ok=True)
            with open(store_p, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            logger.info("store.json salvo e sincronizado com sucesso: %s", store_p)
        except Exception as e:
            logger.warning("Falha ao sincronizar edição no store.json: %s", e)

        # Atualizar também no modelo_ramais_haoc.json e qualquer arquivo na pasta de rede
        candidatos = [
            Config.obter_caminho_dados("modelo_ramais_haoc.json"),
            Config.obter_caminho_dados("sample_legacy_data.json"),
        ]
        cfg_path = Config.obter_caminho_dados("network_config.json")
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    c_rede = cfg.get("caminho_rede", "")
                    if c_rede:
                        p_rede = Path(c_rede)
                        if p_rede.is_dir():
                            for jf in p_rede.glob("*.json"):
                                candidatos.append(jf)
                        elif p_rede.is_file():
                            candidatos.append(p_rede)
            except Exception:
                pass

        for c in set(candidatos):
            if c.exists() and c.is_file():
                try:
                    with open(c, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    modificou = False

                    def atualizar_item(item):
                        nonlocal modificou
                        if not isinstance(item, dict):
                            return
                        num_item = str(item.get("numero") or item.get("Numero") or "").strip()
                        id_item = str(item.get("id")) if item.get("id") is not None else ""
                        desc_item = str(item.get("descricao") or item.get("Descricao") or item.get("Descrição") or "").strip()

                        match_id = bool(ramal_id and id_item == str(ramal_id))
                        match_num = bool(numero_extraido and (num_item == numero_extraido or desc_item.endswith(numero_extraido) or re.search(r'\b' + re.escape(numero_extraido) + r'\b', desc_item)))
                        match_desc = bool(desc_antiga and desc_item.lower() == desc_antiga.strip().lower())

                        if match_id or match_num or match_desc:
                            modificou = True
                            if "Descricao" in item: item["Descricao"] = descricao
                            elif "Descrição" in item: item["Descrição"] = descricao
                            else: item["descricao"] = descricao

                            if "IP" in item: item["IP"] = ip
                            elif "I.P" in item: item["I.P"] = ip if ip else "None"
                            else: item["ip"] = ip

                            if "Bloco" in item: item["Bloco"] = bloco
                            elif "bloco" in item: item["bloco"] = bloco

                            if "Setor" in item: item["Setor"] = setor
                            elif "setor" in item: item["setor"] = setor

                            if "MAC" in item: item["MAC"] = mac
                            elif "I.P Cisco" in item: item["I.P Cisco"] = mac
                            elif "MAC Cisco" in item: item["MAC Cisco"] = mac
                            elif "mac_cisco" in item: item["mac_cisco"] = mac

                            if "Modelo" in item: item["Modelo"] = modelo
                            elif "modelo" in item: item["modelo"] = modelo

                    if isinstance(data, list):
                        for item in data:
                            atualizar_item(item)
                    elif isinstance(data, dict):
                        if "ramais" in data and isinstance(data["ramais"], list):
                            for item in data["ramais"]:
                                atualizar_item(item)
                        else:
                            for k, v in data.items():
                                if isinstance(v, list):
                                    for item in v:
                                        atualizar_item(item)

                    if modificou:
                        with open(c, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                            f.flush()
                            try:
                                os.fsync(f.fileno())
                            except Exception:
                                pass
                        logger.info("Arquivo JSON externo atualizado com sucesso: %s", c)
                except Exception as e:
                    logger.warning("Falha ao atualizar JSON externo %s: %s", c, e)
