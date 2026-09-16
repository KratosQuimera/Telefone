"""
Módulo de Auditoria e Registro de Operações.
Registra todas as ações administrativas, mutações de ramais, logins e backups.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional
from datetime import datetime

from haoc_voip.core.database import db
from haoc_voip.core.models import Auditoria

logger = logging.getLogger("haoc.audit")


def registrar_auditoria(
    acao: str,
    entidade: str,
    entidade_id: str | int | None = None,
    detalhes: Any = None,
    usuario_id: int | None = None,
    ip_origem: str | None = None,
) -> None:
    """
    Insere registro persistente na tabela de auditoria com tratamento de exceção seguro.
    Nunca propaga exceções que interrompam o fluxo principal.
    """
    try:
        detalhes_str = None
        if detalhes is not None:
            if isinstance(detalhes, (dict, list)):
                detalhes_str = json.dumps(detalhes, ensure_ascii=False, default=str)
            else:
                detalhes_str = str(detalhes)

        with db.session_scope() as session:
            reg = Auditoria(
                usuario_id=usuario_id,
                acao=acao.upper(),
                entidade=entidade.lower(),
                entidade_id=str(entidade_id) if entidade_id is not None else None,
                detalhes=detalhes_str,
                ip_origem=ip_origem,
                criado_em=datetime.utcnow(),
            )
            session.add(reg)
            logger.info(
                "Auditoria: [%s] %s %s por usuario_id=%s (ip=%s)",
                acao,
                entidade,
                entidade_id,
                usuario_id,
                ip_origem,
            )
    except Exception as exc:
        logger.error("Falha ao gravar registro de auditoria: %s", exc)
