"""
Rotas de Consulta da Trilha de Auditoria.
Acesso restrito ao perfil ADMINISTRADOR.
"""
from __future__ import annotations

import logging
from flask import Blueprint, render_template, request, session

from haoc_voip.web.app import admin_required
from haoc_voip.core.models import Auditoria
from haoc_voip.core.database import db

logger = logging.getLogger("haoc.routes.auditoria")
auditoria_bp = Blueprint("auditoria", __name__)


@auditoria_bp.route("/")
@admin_required
def index():
    """Exibe o registro cronológico de ações administrativas e do sistema."""
    filtro_acao = request.args.get("acao", "").strip().upper()
    filtro_entidade = request.args.get("entidade", "").strip().lower()

    with db.session_scope() as session_db:
        query = session_db.query(Auditoria)

        if filtro_acao:
            query = query.filter(Auditoria.acao == filtro_acao)
        if filtro_entidade:
            query = query.filter(Auditoria.entidade == filtro_entidade)

        registros = query.order_by(Auditoria.criado_em.desc()).limit(200).all()

        return render_template(
            "auditoria.html",
            registros=[r.to_dict() for r in registros],
            filtro_acao=filtro_acao,
            filtro_entidade=filtro_entidade,
        )
