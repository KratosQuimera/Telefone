"""
Módulo de Autenticação, Controle de Acesso Baseado em Perfis (RBAC) e Hash Seguro.
Protege contra ataques de força bruta com bloqueio temporal de conta.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from sqlalchemy import func

from haoc_voip.config import Config
from haoc_voip.core.models import Usuario, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.audit import registrar_auditoria

logger = logging.getLogger("haoc.auth")


def hash_senha(senha: str) -> str:
    """
    Gera hash seguro com algoritmo PBKDF2-HMAC-SHA256 e salteamento criptográfico aleatório.
    Formato retornado: pbkdf2:sha256:100000$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_hex(16)
    iterations = 100_000
    key = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2:sha256:{iterations}${salt}${key.hex()}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Valida a senha contra o hash armazenado de forma constante contra timing attacks."""
    try:
        parts = senha_hash.split("$")
        if len(parts) != 3:
            return False
        header, salt, expected_hash = parts
        algo, subalgo, iters = header.split(":")
        iterations = int(iters)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(key.hex(), expected_hash)
    except Exception as exc:
        logger.error("Erro ao verificar hash de senha: %s", exc)
        return False


def garantir_usuario_master() -> None:
    """
    Garante a existência e integridade do usuário Master dentro do código:
    - Usuário: Wagner (ou wagner)
    - Senha: SenhaTel@Haoc
    - Perfil: ADMINISTRADOR (Acesso Total Master)
    """
    try:
        with db.session_scope() as session:
            usuario = session.query(Usuario).filter(
                (func.lower(Usuario.login) == "wagner") | (Usuario.login == "Wagner")
            ).first()

            senha_hasheada = hash_senha("SenhaTel@Haoc")

            if not usuario:
                usuario = Usuario(
                    nome="Wagner (Administrador Master)",
                    login="Wagner",
                    senha_hash=senha_hasheada,
                    perfil=PerfilUsuario.ADMINISTRADOR.value,
                    ativo=True,
                    tentativas_falhas=0,
                    bloqueado_ate=None,
                )
                session.add(usuario)
                logger.info("Usuário Master 'Wagner' criado com sucesso com perfil ADMINISTRADOR.")
            else:
                # Sincronizar credenciais e reativar caso necessário
                usuario.senha_hash = senha_hasheada
                usuario.perfil = PerfilUsuario.ADMINISTRADOR.value
                usuario.ativo = True
                usuario.tentativas_falhas = 0
                usuario.bloqueado_ate = None
                if not usuario.nome or "Wagner" not in usuario.nome:
                    usuario.nome = "Wagner (Administrador Master)"
                logger.info("Usuário Master 'Wagner' validado e sincronizado com sucesso.")
    except Exception as exc:
        logger.error("Falha ao garantir usuário master: %s", exc)


def autenticar_usuario(login: str, senha: str, ip_origem: str | None = None) -> Tuple[Optional[Usuario], Optional[str]]:
    """
    Autentica credenciais do usuário.
    Retorna (Usuario, None) em caso de sucesso ou (None, mensagem_erro) em caso de falha.
    Aplica política estrita de lockout após 5 tentativas consecutivas.
    """
    login_input = login.strip()
    login_limpo = login_input.lower()
    agora = datetime.utcnow()

    with db.session_scope() as session:
        usuario = session.query(Usuario).filter(
            (func.lower(Usuario.login) == login_limpo) | (Usuario.login == login_input)
        ).first()

        if not usuario:
            logger.warning("Tentativa de login com usuário inexistente: %s (IP: %s)", login_limpo, ip_origem)
            return None, "Credenciais inválidas."

        if not usuario.ativo:
            logger.warning("Tentativa de login com usuário inativo: %s (IP: %s)", login_limpo, ip_origem)
            return None, "Usuário desativado pelo administrador."

        # Checar bloqueio temporário por tentativas
        if usuario.bloqueado_ate and usuario.bloqueado_ate > agora:
            minutos_restantes = int((usuario.bloqueado_ate - agora).total_seconds() / 60) + 1
            logger.warning("Usuário bloqueado %s tentou login. Restam %s min.", login_limpo, minutos_restantes)
            return None, f"Conta temporariamente bloqueada por excesso de tentativas. Tente novamente em {minutos_restantes} minuto(s)."

        # Validar senha
        if not verificar_senha(senha, usuario.senha_hash):
            usuario.tentativas_falhas += 1
            if usuario.tentativas_falhas >= Config.MAX_LOGIN_ATTEMPTS:
                usuario.bloqueado_ate = agora + timedelta(minutes=Config.LOCKOUT_DURATION_MINUTES)
                logger.error("Conta %s BLOQUEADA por 15 min devido a %s tentativas incorretas.", login_limpo, usuario.tentativas_falhas)
                registrar_auditoria(
                    acao="BLOQUEIO_CONTA",
                    entidade="usuario",
                    entidade_id=usuario.id,
                    detalhes={"motivo": "Excesso de tentativas incorretas"},
                    ip_origem=ip_origem,
                )
                return None, f"Conta bloqueada por excesso de tentativas incorretas ({Config.LOCKOUT_DURATION_MINUTES} min)."
            
            logger.warning("Senha incorreta para %s. Tentativa %s/%s.", login_limpo, usuario.tentativas_falhas, Config.MAX_LOGIN_ATTEMPTS)
            return None, f"Credenciais inválidas ({usuario.tentativas_falhas}/{Config.MAX_LOGIN_ATTEMPTS} tentativas)."

        # Sucesso no login
        usuario.tentativas_falhas = 0
        usuario.bloqueado_ate = None
        usuario.ultimo_login = agora

        # Copiar dados para retorno seguro fora da sessão
        usuario_dict = usuario.to_dict()

        registrar_auditoria(
            acao="LOGIN_SUCESSO",
            entidade="usuario",
            entidade_id=usuario.id,
            detalhes={"perfil": usuario.perfil},
            usuario_id=usuario.id,
            ip_origem=ip_origem,
        )

        return usuario, None


def verificar_permissao(perfil_usuario: str, acao: str) -> bool:
    """
    Avalia a matriz de permissões RBAC:
    - ADMINISTRADOR: Acesso total (CRUD, usuários, configurações, backups, auditoria).
    - ANALISTA: Visualização, varreduras, edição pontual de IP/MAC/observação, exportação de relatórios.
    - VISUALIZACAO: Apenas leitura do dashboard, ramais e relatórios.
    """
    perfil = perfil_usuario.upper()
    
    if perfil == PerfilUsuario.ADMINISTRADOR.value:
        return True

    if perfil == PerfilUsuario.ANALISTA.value:
        return acao in (
            "CONSULTAR",
            "EXECUTAR_VARREDURA",
            "EDITAR_RAMAL_SIMPLES",
            "EXPORTAR_RELATORIO",
            "EXPORTAR_HISTORICO",
            "MARCAR_ALERTA",
            "EXPORTAR_JSON",
        )

    if perfil == PerfilUsuario.VISUALIZACAO.value:
        return acao in (
            "CONSULTAR",
            "EXPORTAR_RELATORIO",
        )

    return False
