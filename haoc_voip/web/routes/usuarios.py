"""
Rotas de Gerenciamento de Usuários e Perfis RBAC.
Acesso restrito ao perfil ADMINISTRADOR.
"""
from __future__ import annotations

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from haoc_voip.web.app import admin_required
from haoc_voip.core.models import Usuario, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.auth import hash_senha
from haoc_voip.core.audit import registrar_auditoria

logger = logging.getLogger("haoc.routes.usuarios")
usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/")
@admin_required
def lista():
    """Exibe a listagem de usuários com seus perfis e status."""
    with db.session_scope() as session_db:
        usuarios = session_db.query(Usuario).order_by(Usuario.nome).all()
        return render_template(
            "usuarios.html",
            usuarios=[u.to_dict() for u in usuarios],
            perfis=[p.value for p in PerfilUsuario],
        )


@usuarios_bp.route("/novo", methods=["POST"])
@admin_required
def criar():
    """Cadastra um novo usuário no sistema."""
    nome = request.form.get("nome", "").strip()
    login = request.form.get("login", "").strip().lower()
    senha = request.form.get("senha", "").strip()
    perfil = request.form.get("perfil", PerfilUsuario.ANALISTA.value)

    if not nome or not login or not senha:
        flash("Todos os campos são obrigatórios.", "warning")
        return redirect(url_for("usuarios.lista"))

    with db.session_scope() as session_db:
        existente = session_db.query(Usuario).filter(Usuario.login == login).first()
        if existente:
            flash(f"O login '{login}' já está em uso.", "danger")
            return redirect(url_for("usuarios.lista"))

        novo = Usuario(
            nome=nome,
            login=login,
            senha_hash=hash_senha(senha),
            perfil=perfil,
            ativo=True,
        )
        session_db.add(novo)
        session_db.flush()
        uid = novo.id

    registrar_auditoria(
        acao="CRIAR_USUARIO",
        entidade="usuario",
        entidade_id=uid,
        detalhes={"login": login, "perfil": perfil},
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash(f"Usuário '{login}' cadastrado com sucesso.", "success")
    return redirect(url_for("usuarios.lista"))


@usuarios_bp.route("/<int:user_id>/alterar-senha", methods=["POST"])
@admin_required
def alterar_senha(user_id: int):
    """Redefine a senha de um usuário."""
    nova_senha = request.form.get("nova_senha", "").strip()
    if not nova_senha or len(nova_senha) < 6:
        flash("A senha deve conter no mínimo 6 caracteres.", "warning")
        return redirect(url_for("usuarios.lista"))

    with db.session_scope() as session_db:
        u = session_db.query(Usuario).filter(Usuario.id == user_id).first()
        if not u:
            flash("Usuário não encontrado.", "danger")
            return redirect(url_for("usuarios.lista"))

        u.senha_hash = hash_senha(nova_senha)
        u.tentativas_falhas = 0
        u.bloqueado_ate = None

    registrar_auditoria(
        acao="REDEFINIR_SENHA_USUARIO",
        entidade="usuario",
        entidade_id=user_id,
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash("Senha redefinida com sucesso.", "success")
    return redirect(url_for("usuarios.lista"))


@usuarios_bp.route("/<int:user_id>/toggle-ativo", methods=["POST"])
@admin_required
def toggle_ativo(user_id: int):
    """Ativa ou desativa o acesso de um usuário."""
    if user_id == session.get("usuario_id"):
        flash("Você não pode desativar seu próprio usuário.", "danger")
        return redirect(url_for("usuarios.lista"))

    with db.session_scope() as session_db:
        u = session_db.query(Usuario).filter(Usuario.id == user_id).first()
        if not u:
            flash("Usuário não encontrado.", "danger")
            return redirect(url_for("usuarios.lista"))

        u.ativo = not u.ativo
        status_txt = "reativado" if u.ativo else "desativado"

    registrar_auditoria(
        acao=f"USUARIO_{status_txt.upper()}",
        entidade="usuario",
        entidade_id=user_id,
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash(f"Usuário {status_txt} com sucesso.", "info")
    return redirect(url_for("usuarios.lista"))
