"""
Fábrica de Aplicação Flask para o HAOC VoIP Monitor Enterprise.
Interface Web corporativa com Jinja2, HTML5, CSS3, JavaScript e autenticação RBAC.
"""
from __future__ import annotations

import functools
import logging
from datetime import datetime, timedelta
from typing import Callable, Any

from flask import (
    Flask,
    session,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
    render_template,
    g,
)

from haoc_voip.config import Config
from haoc_voip.core.models import Usuario, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.monitor import monitor_engine

logger = logging.getLogger("haoc.web")


def login_required(view_func: Callable) -> Callable:
    """Decorador para exigir usuário autenticado na sessão."""
    @functools.wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any):
        if "usuario_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"erro": "Autenticação obrigatória.", "codigo": "UNAUTHORIZED"}), 401
            return redirect(url_for("auth.login", next=request.url))
        return view_func(*args, **kwargs)
    return wrapper


def admin_required(view_func: Callable) -> Callable:
    """Decorador para exigir perfil de ADMINISTRADOR."""
    @functools.wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any):
        if "usuario_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"erro": "Autenticação obrigatória."}), 401
            return redirect(url_for("auth.login", next=request.url))

        if session.get("perfil") != PerfilUsuario.ADMINISTRADOR.value:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"erro": "Permissão negada. Apenas Administradores podem executar esta ação."}), 403
            flash("Acesso restrito ao perfil de Administrador.", "danger")
            return redirect(url_for("dashboard.index"))

        return view_func(*args, **kwargs)
    return wrapper


def analista_ou_admin_required(view_func: Callable) -> Callable:
    """Decorador para exigir perfil ANALISTA ou ADMINISTRADOR."""
    @functools.wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any):
        if "usuario_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"erro": "Autenticação obrigatória."}), 401
            return redirect(url_for("auth.login", next=request.url))

        perfil = session.get("perfil")
        if perfil not in (PerfilUsuario.ADMINISTRADOR.value, PerfilUsuario.ANALISTA.value):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"erro": "Permissão negada para o perfil de Visualização."}), 403
            flash("Seu perfil possui apenas permissão de visualização.", "warning")
            return redirect(url_for("dashboard.index"))

        return view_func(*args, **kwargs)
    return wrapper


def create_app(config_override: dict | None = None) -> Flask:
    """Cria e configura a instância Flask."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
    if config_override:
        app.config.update(config_override)

    # Injetar variáveis de contexto globais para todos os templates Jinja2
    @app.context_processor
    def inject_globals():
        return {
            "app_name": "HAOC VoIP Monitor Enterprise",
            "hospital_name": "Hospital das Clínicas - HAOC",
            "now_year": datetime.utcnow().year,
            "current_user": {
                "id": session.get("usuario_id"),
                "nome": session.get("usuario_nome"),
                "login": session.get("usuario_login"),
                "perfil": session.get("perfil"),
                "is_admin": session.get("perfil") == PerfilUsuario.ADMINISTRADOR.value,
                "is_analista": session.get("perfil") in (PerfilUsuario.ADMINISTRADOR.value, PerfilUsuario.ANALISTA.value),
            },
        }

    # Carregar dados do usuário na requisição se autenticado
    @app.before_request
    def carregar_usuario_atual():
        g.usuario = None
        if "usuario_id" in session:
            g.usuario_id = session["usuario_id"]
            g.usuario_nome = session.get("usuario_nome")
            g.perfil = session.get("perfil")

    # Registro de Blueprints
    from haoc_voip.web.routes.auth import auth_bp
    from haoc_voip.web.routes.dashboard import dashboard_bp
    from haoc_voip.web.routes.ramais import ramais_bp
    from haoc_voip.web.routes.incidentes import incidentes_bp
    from haoc_voip.web.routes.importacao import importacao_bp
    from haoc_voip.web.routes.relatorios import relatorios_bp
    from haoc_voip.web.routes.configuracoes import configuracoes_bp
    from haoc_voip.web.routes.usuarios import usuarios_bp
    from haoc_voip.web.routes.auditoria import auditoria_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ramais_bp, url_prefix="/ramais")
    app.register_blueprint(incidentes_bp, url_prefix="/incidentes")
    app.register_blueprint(importacao_bp, url_prefix="/importacao")
    app.register_blueprint(relatorios_bp, url_prefix="/relatorios")
    app.register_blueprint(configuracoes_bp, url_prefix="/configuracoes")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(auditoria_bp, url_prefix="/auditoria")

    # Tratamento customizado de erros HTTP
    @app.errorhandler(404)
    def pagina_nao_encontrada(e):
        if request.is_json:
            return jsonify({"erro": "Recurso não encontrado."}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def erro_servidor(e):
        logger.error("Erro interno do servidor: %s", e)
        if request.is_json:
            return jsonify({"erro": "Erro interno do servidor."}), 500
        return render_template("500.html", erro=str(e)), 500

    return app
