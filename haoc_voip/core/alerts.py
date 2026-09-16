"""
Módulo de Gestão de Alertas e Notificações (Web, Desktop e E-mail SMTP).
Implementa deduplicação estrita de incidentes abertos e confirmação de leitura.
"""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional

from haoc_voip.config import Config
from haoc_voip.core.database import db
from haoc_voip.core.models import Alerta, Ramal, Incidente

logger = logging.getLogger("haoc.alerts")


class AlertManager:
    """Gerenciador central de alertas com deduplicação."""

    def notificar_queda(self, ramal_id: int, incidente_id: int, offline_segundos: int) -> Optional[Alerta]:
        """
        Gera alerta de queda caso não exista alerta ativo para o mesmo incidente aberto.
        Respeita o tempo mínimo configurado para disparar alerta.
        """
        if offline_segundos < Config.ALERT_MIN_OFFLINE_SECONDS:
            logger.debug(
                "Ramal %s offline por %ss (abaixo do limiar de alerta %ss).",
                ramal_id,
                offline_segundos,
                Config.ALERT_MIN_OFFLINE_SECONDS,
            )
            return None

        with db.session_scope() as session:
            # 1. Deduplicação: checar se já existe alerta para este mesmo incidente
            if incidente_id:
                alerta_existente = session.query(Alerta).filter(
                    Alerta.incidente_id == incidente_id,
                    Alerta.tipo == "QUEDA",
                ).first()
                if alerta_existente:
                    logger.debug("Alerta para incidente %s já emitido anteriormente (deduplicado).", incidente_id)
                    return None

            ramal = session.query(Ramal).filter(Ramal.id == ramal_id).first()
            if not ramal:
                return None

            msg = (
                f"Ramal {ramal.descricao} (IP: {ramal.ip or 'Sem IP'}, Bloco: {ramal.bloco}) "
                f"encontra-se OFFLINE há {Ramal._format_duration(offline_segundos)}."
            )

            novo_alerta = Alerta(
                ramal_id=ramal.id,
                incidente_id=incidente_id,
                tipo="CRITICO" if ramal.criticidade == "CRITICA" else "QUEDA",
                mensagem=msg,
                criado_em=datetime.utcnow(),
                lido=False,
            )
            session.add(novo_alerta)
            session.flush()
            alerta_id = novo_alerta.id
            logger.warning("Novo alerta gerado [#%s]: %s", alerta_id, msg)

        # Enviar e-mail se configurado
        if Config.ALERT_EMAIL_ENABLED:
            self._enviar_email_alerta(f"[ALERTA HAOC VOIP] Queda - {ramal.descricao}", msg)

        return novo_alerta

    def notificar_recuperacao(self, ramal_id: int, incidente_id: int, duracao_segundos: int) -> None:
        """Gera alerta informativo de restabelecimento do ramal."""
        with db.session_scope() as session:
            ramal = session.query(Ramal).filter(Ramal.id == ramal_id).first()
            if not ramal:
                return

            msg = (
                f"Ramal {ramal.descricao} (Bloco: {ramal.bloco}) retornou ONLINE. "
                f"Duração da indisponibilidade: {Ramal._format_duration(duracao_segundos)}."
            )
            novo_alerta = Alerta(
                ramal_id=ramal.id,
                incidente_id=incidente_id,
                tipo="RECUPERACAO",
                mensagem=msg,
                criado_em=datetime.utcnow(),
                lido=False,
            )
            session.add(novo_alerta)
            logger.info("Alerta de recuperação [#%s]: %s", novo_alerta.id, msg)

    def marcar_como_lido(self, alerta_id: int, usuario_nome: str = "Analista") -> bool:
        """Marca um alerta como confirmado/lido."""
        with db.session_scope() as session:
            alerta = session.query(Alerta).filter(Alerta.id == alerta_id).first()
            if alerta:
                alerta.lido = True
                alerta.lido_em = datetime.utcnow()
                alerta.lido_por = usuario_nome
                return True
        return False

    def marcar_todos_lidos(self, usuario_nome: str = "Analista") -> int:
        """Marca todos os alertas pendentes como lidos."""
        with db.session_scope() as session:
            alertas = session.query(Alerta).filter(Alerta.lido == False).all()
            for a in alertas:
                a.lido = True
                a.lido_em = datetime.utcnow()
                a.lido_por = usuario_nome
            return len(alertas)

    def listar_alertas(self, apenas_nao_lidos: bool = True, limite: int = 50) -> List[Dict[str, Any]]:
        """Lista alertas recentes para a interface web e desktop."""
        with db.session_scope() as session:
            q = session.query(Alerta)
            if apenas_nao_lidos:
                q = q.filter(Alerta.lido == False)
            itens = q.order_by(Alerta.criado_em.desc()).limit(limite).all()
            return [it.to_dict() for it in itens]

    def _enviar_email_alerta(self, assunto: str, corpo: str) -> bool:
        """Envio assíncrono ou seguro de e-mail via SMTP configurado."""
        if not Config.SMTP_HOST:
            return False
        try:
            msg = MIMEMultipart()
            msg["From"] = Config.SMTP_FROM
            msg["To"] = Config.SMTP_TO
            msg["Subject"] = assunto
            msg.attach(MIMEText(corpo, "plain", "utf-8"))

            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10) as server:
                if Config.SMTP_USER and Config.SMTP_PASS:
                    server.starttls()
                    server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.sendmail(Config.SMTP_FROM, [Config.SMTP_TO], msg.as_string())
            logger.info("E-mail de alerta enviado para %s", Config.SMTP_TO)
            return True
        except Exception as exc:
            logger.error("Falha no envio de e-mail SMTP: %s", exc)
            return False


alert_mgr = AlertManager()
