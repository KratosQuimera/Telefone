"""
Rotas de Autenticação e Gestão de Sessão.
"""
from __future__ import annotations

import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from haoc_voip.core.auth import autenticar_usuario, hash_senha, verificar_senha
from haoc_voip.core.database import db
from haoc_voip.core.models import Usuario
from haoc_voip.core.audit import registrar_auditoria

logger = logging.getLogger("haoc.routes.auth")
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Tela e processamento de login seguro."""
    if "usuario_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        login_user = request.form.get("login", "").strip()
        senha = request.form.get("senha", "")
        ip_origem = request.remote_addr

        if not login_user or not senha:
            flash("Informe o usuário e a senha.", "warning")
            return render_template("login.html")

        usuario, erro = autenticar_usuario(login_user, senha, ip_origem=ip_origem)
        if erro:
            flash(erro, "danger")
            return render_template("login.html", login_preenchido=login_user)

        # Configurar sessão
        session.clear()
        session.permanent = True
        session["usuario_id"] = usuario.id
        session["usuario_nome"] = usuario.nome
        session["usuario_login"] = usuario.login
        session["perfil"] = usuario.perfil

        flash(f"Bem-vindo(a), {usuario.nome}!", "success")
        next_url = request.args.get("next")
        if next_url and not next_url.startswith("//") and not next_url.startswith("http"):
            return redirect(next_url)
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Encerra a sessão e registra logout na auditoria."""
    uid = session.get("usuario_id")
    if uid:
        registrar_auditoria(
            acao="LOGOUT",
            entidade="usuario",
            entidade_id=uid,
            usuario_id=uid,
            ip_origem=request.remote_addr,
        )
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("auth.login"))
