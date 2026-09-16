"""
Rotas do Dashboard Principal e APIs JSON assíncronas para atualização em tempo real.
"""
from __future__ import annotations

import logging
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, session

from haoc_voip.web.app import login_required, analista_ou_admin_required
from haoc_voip.core.models import Ramal, Bloco, Setor, Incidente, StatusRamal
from haoc_voip.core.database import db
from haoc_voip.core.monitor import monitor_engine, executar_ping
from haoc_voip.core.alerts import alert_mgr

logger = logging.getLogger("haoc.routes.dashboard")
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Renderiza a página principal do dashboard."""
    with db.session_scope() as session_db:
        blocos = session_db.query(Bloco).filter(Bloco.ativo == True).order_by(Bloco.nome).all()
        setores = session_db.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()
        blocos_list = [b.nome for b in blocos]
        setores_list = [s.nome for s in setores]

    return render_template(
        "dashboard.html",
        blocos_disponiveis=blocos_list,
        setores_disponiveis=setores_list,
    )


@dashboard_bp.route("/api/stats")
@login_required
def api_stats():
    """Retorna estatísticas operacionais em tempo real para polling via AJAX."""
    stats = monitor_engine.calcular_estatisticas()
    return jsonify(stats)


@dashboard_bp.route("/api/ramais")
@login_required
def api_ramais():
    """
    Retorna a lista completa ou filtrada de ramais com seus metadados operacionais.
    Suporta busca rápida por texto (descrição, IP, MAC) e filtros por bloco, status e setor.
    """
    busca = request.args.get("busca", "").strip().lower()
    filtro_bloco = request.args.get("bloco", "").strip()
    filtro_status = request.args.get("status", "").strip().upper()
    filtro_setor = request.args.get("setor", "").strip()
    ordenacao = request.args.get("ordenar", "status")  # status, descricao, duracao_offline, bloco

    with db.session_scope() as session_db:
        query = session_db.query(Ramal)

        if filtro_bloco:
            query = query.filter(Ramal.bloco == filtro_bloco)
        if filtro_status:
            if filtro_status == "INATIVO":
                query = query.filter(Ramal.ativo == False)
            else:
                query = query.filter(Ramal.ativo == True, Ramal.status_atual == filtro_status)
        if filtro_setor:
            query = query.filter(Ramal.setor == filtro_setor)

        ramais_obj = query.all()
        ramais_data = [r.to_dict() for r in ramais_obj]

    # Filtragem textual em memória para velocidade e regex flexível
    if busca:
        ramais_data = [
            r for r in ramais_data
            if busca in r["descricao"].lower()
            or busca in (r["ip"] or "").lower()
            or busca in (r["mac_cisco"] or "").lower()
            or busca in (r["modelo"] or "").lower()
        ]

    # Ordenação
    if ordenacao == "descricao":
        ramais_data.sort(key=lambda x: x["descricao"].lower())
    elif ordenacao == "duracao_offline":
        ramais_data.sort(key=lambda x: x["duracao_offline_segundos"], reverse=True)
    elif ordenacao == "bloco":
        ramais_data.sort(key=lambda x: (x["bloco"].lower(), x["descricao"].lower()))
    else:  # Padrão: agrupar por OFFLINE primeiro (crítico), depois AGUARDANDO, ONLINE, INATIVO
        prioridade = {"OFFLINE": 1, "AGUARDANDO": 2, "ONLINE": 3, "INATIVO": 4}
        ramais_data.sort(key=lambda x: (prioridade.get(x["status"], 5), x["bloco"], x["descricao"]))

    # Agrupamento por bloco para visualização em cartões
    por_bloco = {}
    for r in ramais_data:
        b = r["bloco"]
        if b not in por_bloco:
            por_bloco[b] = []
        por_bloco[b].append(r)

    return jsonify({
        "total": len(ramais_data),
        "ramais": ramais_data,
        "por_bloco": por_bloco,
    })


@dashboard_bp.route("/api/scan/start", methods=["POST"])
@analista_ou_admin_required
def api_start_scan():
    """Dispara uma varredura sob demanda no motor de monitoramento."""
    if monitor_engine.em_execucao:
        return jsonify({"erro": "Uma varredura já está em execução."}), 400

    import threading
    threading.Thread(target=monitor_engine.executar_varredura, daemon=True).start()
    return jsonify({"mensagem": "Varredura iniciada com sucesso em segundo plano."})


@dashboard_bp.route("/api/scan/cancel", methods=["POST"])
@analista_ou_admin_required
def api_cancel_scan():
    """Cancela a varredura em andamento com segurança."""
    monitor_engine.cancelar_varredura()
    return jsonify({"mensagem": "Cancelamento solicitado com sucesso."})


@dashboard_bp.route("/api/ramais/<int:ramal_id>/ping", methods=["POST"])
@analista_ou_admin_required
def api_ping_individual(ramal_id: int):
    """Executa um teste imediato de ping pontual para um único ramal."""
    with db.session_scope() as session_db:
        ramal = session_db.query(Ramal).filter(Ramal.id == ramal_id).first()
        if not ramal:
            return jsonify({"erro": "Ramal não encontrado."}), 404
        ip = ramal.ip

    if not ip:
        return jsonify({"sucesso": False, "erro": "Ramal não possui IP configurado."})

    sucesso, latencia, erro = executar_ping(ip, timeout_seconds=2.0, retries=2)
    return jsonify({
        "sucesso": sucesso,
        "ip": ip,
        "latencia": latencia,
        "erro": erro,
    })


@dashboard_bp.route("/api/alertas")
@login_required
def api_alertas():
    """Retorna alertas operacionais não lidos."""
    alertas = alert_mgr.listar_alertas(apenas_nao_lidos=True, limite=20)
    return jsonify({"alertas": alertas, "total": len(alertas)})


@dashboard_bp.route("/api/alertas/<int:alerta_id>/read", methods=["POST"])
@analista_ou_admin_required
def api_alerta_read(alerta_id: int):
    """Marca um alerta específico como lido."""
    user_name = session.get("usuario_nome", "Analista")
    sucesso = alert_mgr.marcar_como_lido(alerta_id, usuario_nome=user_name)
    return jsonify({"sucesso": sucesso})


@dashboard_bp.route("/api/alertas/read-all", methods=["POST"])
@analista_ou_admin_required
def api_alerta_read_all():
    """Marca todos os alertas pendentes como lidos."""
    user_name = session.get("usuario_nome", "Analista")
    qtd = alert_mgr.marcar_todos_lidos(usuario_nome=user_name)
    return jsonify({"sucesso": True, "total_lidos": qtd})
