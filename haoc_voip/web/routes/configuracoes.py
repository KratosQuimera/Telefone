"""
Rotas de Parâmetros Operacionais, Backups e Configurações do Sistema.
Acesso restrito ao perfil ADMINISTRADOR.
"""
from __future__ import annotations

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session

from haoc_voip.web.app import admin_required
from haoc_voip.config import Config
from haoc_voip.core.models import Configuracao
from haoc_voip.core.database import db
from haoc_voip.core.backup import backup_mgr
from haoc_voip.core.audit import registrar_auditoria

logger = logging.getLogger("haoc.routes.configuracoes")
configuracoes_bp = Blueprint("configuracoes", __name__)


@configuracoes_bp.route("/")
@admin_required
def index():
    """Tela de configurações do sistema e gerenciamento de snapshots/backups."""
    with db.session_scope() as session_db:
        configs = session_db.query(Configuracao).all()
        config_map = {c.chave: c.valor for c in configs}

    backups = backup_mgr.listar_backups()

    return render_template(
        "configuracoes.html",
        configs=config_map,
        backups=backups,
        retention_days=Config.BACKUP_RETENTION_DAYS,
        max_backups=Config.MAX_BACKUPS_COUNT,
    )


@configuracoes_bp.route("/salvar", methods=["POST"])
@admin_required
def salvar():
    """Salva parâmetros de rede, monitoramento e alertas."""
    ping_timeout = request.form.get("ping_timeout", "1.5").strip()
    ping_retries = request.form.get("ping_retries", "2").strip()
    scan_interval = request.form.get("scan_interval", "60").strip()
    max_threads = request.form.get("max_threads", "25").strip()
    alert_min_offline = request.form.get("alert_min_offline", "120").strip()
    hospital_name = request.form.get("hospital_name", "Hospital das Clínicas - HAOC").strip()

    novas_configs = {
        "ping_timeout": ping_timeout,
        "ping_retries": ping_retries,
        "scan_interval": scan_interval,
        "max_threads": max_threads,
        "alert_min_offline": alert_min_offline,
        "hospital_name": hospital_name,
    }

    with db.session_scope() as session_db:
        for k, v in novas_configs.items():
            item = session_db.query(Configuracao).filter(Configuracao.chave == k).first()
            if item:
                item.valor = v
            else:
                session_db.add(Configuracao(chave=k, valor=v))

    # Atualizar variáveis em memória
    try:
        Config.DEFAULT_PING_TIMEOUT = float(ping_timeout)
        Config.DEFAULT_PING_RETRIES = int(ping_retries)
        Config.DEFAULT_SCAN_INTERVAL = int(scan_interval)
        Config.MAX_CONCURRENT_THREADS = int(max_threads)
        Config.ALERT_MIN_OFFLINE_SECONDS = int(alert_min_offline)
    except ValueError as e:
        flash(f"Atenção aos valores numéricos: {e}", "warning")

    registrar_auditoria(
        acao="ALTERAR_CONFIGURACOES",
        entidade="configuracao",
        detalhes=novas_configs,
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash("Parâmetros do sistema salvos com sucesso.", "success")
    return redirect(url_for("configuracoes.index"))


@configuracoes_bp.route("/backup/criar", methods=["POST"])
@admin_required
def criar_backup():
    """Executa um backup manual instantâneo do banco."""
    motivo = request.form.get("motivo", "manual").strip()
    usuario_id = session.get("usuario_id")

    bkp_path = backup_mgr.criar_backup(motivo=motivo, usuario_id=usuario_id)
    if bkp_path:
        flash(f"Backup '{bkp_path.name}' gerado com sucesso!", "success")
    else:
        flash("Falha ao gerar cópia de backup do banco de dados.", "danger")

    return redirect(url_for("configuracoes.index"))


@configuracoes_bp.route("/backup/restaurar", methods=["POST"])
@admin_required
def restaurar_backup():
    """Restaura o banco a partir de um backup pré-existente."""
    arquivo = request.form.get("arquivo_backup", "").strip()
    usuario_id = session.get("usuario_id")

    if not arquivo:
        flash("Nenhum arquivo de backup selecionado.", "warning")
        return redirect(url_for("configuracoes.index"))

    sucesso = backup_mgr.restaurar_backup(arquivo, usuario_id=usuario_id)
    if sucesso:
        flash(f"Banco de dados restaurado com sucesso a partir de {arquivo}!", "success")
    else:
        flash(f"Falha ao restaurar backup {arquivo}. Verifique o log de integridade.", "danger")

    return redirect(url_for("configuracoes.index"))
