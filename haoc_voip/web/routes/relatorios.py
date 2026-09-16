"""
Rotas de Relatórios Operacionais, SLA e Análise de Disponibilidade.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, Response, session
from sqlalchemy import func

from haoc_voip.web.app import login_required
from haoc_voip.core.models import Ramal, Bloco, Incidente, StatusRamal
from haoc_voip.core.database import db

logger = logging.getLogger("haoc.routes.relatorios")
relatorios_bp = Blueprint("relatorios", __name__)


@relatorios_bp.route("/")
@login_required
def index():
    """Gera visualização de relatórios gerenciais e SLA por bloco."""
    periodo_dias = request.args.get("dias", default=30, type=int)
    data_corte = datetime.utcnow() - timedelta(days=periodo_dias)

    with db.session_scope() as session_db:
        # Total de incidentes no período
        total_incidentes = session_db.query(Incidente).filter(Incidente.iniciado_em >= data_corte).count()

        # Tempo total de indisponibilidade em segundos
        tempo_total_off = (
            session_db.query(func.coalesce(func.sum(Incidente.duracao), 0))
            .filter(Incidente.iniciado_em >= data_corte)
            .scalar()
        )

        # Ranking de ramais com mais falhas
        ranking_quedas = (
            session_db.query(
                Ramal.id,
                Ramal.descricao,
                Ramal.bloco,
                Ramal.ip,
                Ramal.criticidade,
                func.count(Incidente.id).label("quedas"),
                func.coalesce(func.sum(Incidente.duracao), 0).label("tempo_off"),
            )
            .join(Incidente, Incidente.ramal_id == Ramal.id)
            .filter(Incidente.iniciado_em >= data_corte)
            .group_by(Ramal.id)
            .order_by(func.count(Incidente.id).desc())
            .limit(10)
            .all()
        )

        ranking_formatado = [
            {
                "id": r[0],
                "descricao": r[1],
                "bloco": r[2],
                "ip": r[3],
                "criticidade": r[4],
                "quedas": r[5],
                "tempo_off_segundos": r[6],
                "tempo_off_formatado": Ramal._format_duration(r[6]),
            }
            for r in ranking_quedas
        ]

        # Estatísticas agregadas por bloco
        blocos = session_db.query(Bloco).filter(Bloco.ativo == True).all()
        relatorio_blocos = []

        for b in blocos:
            ramais_bloco = session_db.query(Ramal).filter(Ramal.bloco == b.nome, Ramal.ativo == True).all()
            tot = len(ramais_bloco)
            online_count = sum(1 for ram in ramais_bloco if ram.status_atual == StatusRamal.ONLINE.value)
            
            # Incidentes deste bloco no período
            inc_bloco = (
                session_db.query(func.count(Incidente.id), func.coalesce(func.sum(Incidente.duracao), 0))
                .join(Ramal, Incidente.ramal_id == Ramal.id)
                .filter(Ramal.bloco == b.nome, Incidente.iniciado_em >= data_corte)
                .first()
            )
            qtd_inc = inc_bloco[0] if inc_bloco else 0
            seg_inc = inc_bloco[1] if inc_bloco else 0

            disponibilidade_atual = round((online_count / tot * 100), 1) if tot > 0 else 100.0

            relatorio_blocos.append({
                "bloco": b.nome,
                "cor": b.cor,
                "total_ramais": tot,
                "online": online_count,
                "offline": tot - online_count,
                "disponibilidade_atual": disponibilidade_atual,
                "quedas_periodo": qtd_inc,
                "tempo_total_offline_formatado": Ramal._format_duration(seg_inc),
            })

    return render_template(
        "relatorios.html",
        periodo_dias=periodo_dias,
        total_incidentes=total_incidentes,
        tempo_total_off_formatado=Ramal._format_duration(tempo_total_off),
        ranking=ranking_formatado,
        relatorio_blocos=relatorio_blocos,
    )


@relatorios_bp.route("/exportar/csv")
@login_required
def exportar_sla_csv():
    """Exporta relatório de SLA em formato CSV."""
    periodo_dias = request.args.get("dias", default=30, type=int)
    data_corte = datetime.utcnow() - timedelta(days=periodo_dias)

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    writer.writerow(["Bloco", "Total Ramais", "Online", "Offline", "Disponibilidade Atual (%)", "Quedas no Período"])

    with db.session_scope() as session_db:
        blocos = session_db.query(Bloco).filter(Bloco.ativo == True).all()
        for b in blocos:
            ramais = session_db.query(Ramal).filter(Ramal.bloco == b.nome, Ramal.ativo == True).all()
            tot = len(ramais)
            on = sum(1 for r in ramais if r.status_atual == StatusRamal.ONLINE.value)
            disp = round((on / tot * 100), 1) if tot > 0 else 100.0
            
            qtd_inc = (
                session_db.query(func.count(Incidente.id))
                .join(Ramal, Incidente.ramal_id == Ramal.id)
                .filter(Ramal.bloco == b.nome, Incidente.iniciado_em >= data_corte)
                .scalar() or 0
            )
            writer.writerow([b.nome, tot, on, tot - on, f"{disp}%", qtd_inc])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=relatorio_sla_haoc_{timestamp}.csv"},
    )
