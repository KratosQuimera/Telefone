"""
Rotas de Gerenciamento e CRUD de Ramais VoIP Cisco.
Validação estrita de IPv4, MAC Cisco, campos obrigatórios, duplicidades e auditoria.
"""
from __future__ import annotations

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session

from haoc_voip.web.app import login_required, admin_required, analista_ou_admin_required
from haoc_voip.core.models import Ramal, Bloco, Setor, Incidente, Monitoramento, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.importer import validar_ipv4, normalizar_mac, MAC_CISCO_REGEX
from haoc_voip.core.audit import registrar_auditoria
from haoc_voip.core.backup import backup_mgr

logger = logging.getLogger("haoc.routes.ramais")
ramais_bp = Blueprint("ramais", __name__)


@ramais_bp.route("/")
@login_required
def lista():
    """Tela de listagem e pesquisa tabular de ramais."""
    with db.session_scope() as session_db:
        ramais = session_db.query(Ramal).order_by(Ramal.bloco, Ramal.descricao).all()
        blocos = session_db.query(Bloco).filter(Bloco.ativo == True).order_by(Bloco.nome).all()
        setores = session_db.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()
        
        return render_template(
            "ramais.html",
            ramais=[r.to_dict() for r in ramais],
            blocos=[b.to_dict() for b in blocos],
            setores=[s.to_dict() for s in setores],
        )


@ramais_bp.route("/<int:ramal_id>")
@login_required
def detalhe(ramal_id: int):
    """Página detalhada de um ramal com histórico de incidentes e latências."""
    with db.session_scope() as session_db:
        ramal = session_db.query(Ramal).filter(Ramal.id == ramal_id).first()
        if not ramal:
            flash("Ramal não encontrado.", "danger")
            return redirect(url_for("ramais.lista"))

        # Últimos incidentes deste ramal
        incidentes = (
            session_db.query(Incidente)
            .filter(Incidente.ramal_id == ramal_id)
            .order_by(Incidente.iniciado_em.desc())
            .limit(20)
            .all()
        )

        # Últimas leituras de monitoramento (latência)
        monitoramentos = (
            session_db.query(Monitoramento)
            .filter(Monitoramento.ramal_id == ramal_id)
            .order_by(Monitoramento.verificado_em.desc())
            .limit(30)
            .all()
        )

        blocos = session_db.query(Bloco).filter(Bloco.ativo == True).order_by(Bloco.nome).all()
        setores = session_db.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()

        return render_template(
            "ramal_detail.html",
            ramal=ramal.to_dict(),
            incidentes=[i.to_dict() for i in incidentes],
            monitoramentos=[m.to_dict() for m in monitoramentos],
            blocos=[b.to_dict() for b in blocos],
            setores=[s.to_dict() for s in setores],
        )


@ramais_bp.route("/novo", methods=["POST"])
@admin_required
def criar():
    """Cadastra um novo ramal com validações e auditoria."""
    descricao = request.form.get("descricao", "").strip()
    bloco = request.form.get("bloco", "").strip()
    ip = request.form.get("ip", "").strip()
    mac = normalizar_mac(request.form.get("mac_cisco", ""))
    modelo = request.form.get("modelo", "").strip() or "Cisco CP-7821"
    setor = request.form.get("setor", "").strip()
    localizacao = request.form.get("localizacao", "").strip()
    criticidade = request.form.get("criticidade", "NORMAL").upper()
    observacoes = request.form.get("observacoes", "").strip()

    if not descricao:
        flash("A descrição do ramal é obrigatória.", "danger")
        return redirect(url_for("ramais.lista"))

    if not bloco:
        flash("O bloco é obrigatório.", "danger")
        return redirect(url_for("ramais.lista"))

    if ip and not validar_ipv4(ip):
        flash(f"O endereço IP '{ip}' não é um IPv4 válido.", "danger")
        return redirect(url_for("ramais.lista"))

    if mac and not MAC_CISCO_REGEX.match(mac):
        flash(f"O endereço MAC '{mac}' possui formato inválido.", "danger")
        return redirect(url_for("ramais.lista"))

    # Checagem de duplicidades
    with db.session_scope() as session_db:
        if ip:
            dup_ip = session_db.query(Ramal).filter(Ramal.ip == ip, Ramal.ativo == True).first()
            if dup_ip:
                flash(f"O IP {ip} já está cadastrado no ramal '{dup_ip.descricao}'.", "warning")
                return redirect(url_for("ramais.lista"))

        if mac:
            dup_mac = session_db.query(Ramal).filter(Ramal.mac_cisco == mac, Ramal.ativo == True).first()
            if dup_mac:
                flash(f"O MAC {mac} já está cadastrado no ramal '{dup_mac.descricao}'.", "warning")
                return redirect(url_for("ramais.lista"))

        # Backup preventivo antes da gravação
        backup_mgr.criar_backup(motivo="pre_criar_ramal", usuario_id=session.get("usuario_id"))

        novo = Ramal(
            descricao=descricao,
            bloco=bloco,
            ip=ip or None,
            mac_cisco=mac or None,
            modelo=modelo,
            setor=setor or None,
            localizacao=localizacao or None,
            criticidade=criticidade if criticidade in ("NORMAL", "ALTA", "CRITICA") else "NORMAL",
            observacoes=observacoes or None,
            ativo=True,
        )
        session_db.add(novo)
        session_db.flush()
        novo_id = novo.id

    registrar_auditoria(
        acao="CRIAR_RAMAL",
        entidade="ramal",
        entidade_id=novo_id,
        detalhes={"descricao": descricao, "ip": ip, "mac": mac, "bloco": bloco},
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash(f"Ramal '{descricao}' cadastrado com sucesso!", "success")
    return redirect(url_for("ramais.lista"))


@ramais_bp.route("/<int:ramal_id>/editar", methods=["POST"])
@analista_ou_admin_required
def editar(ramal_id: int):
    """Edição de ramal. Analistas podem alterar IP, MAC e observações. Admins alteram tudo."""
    is_admin = session.get("perfil") == PerfilUsuario.ADMINISTRADOR.value

    with db.session_scope() as session_db:
        ramal = session_db.query(Ramal).filter(Ramal.id == ramal_id).first()
        if not ramal:
            flash("Ramal não encontrado.", "danger")
            return redirect(url_for("ramais.lista"))

        ip = request.form.get("ip", "").strip()
        mac = normalizar_mac(request.form.get("mac_cisco", ""))
        observacoes = request.form.get("observacoes", "").strip()

        if ip and not validar_ipv4(ip):
            flash(f"O endereço IP '{ip}' não é um IPv4 válido.", "danger")
            return redirect(url_for("ramais.detalhe", ramal_id=ramal_id))

        if mac and not MAC_CISCO_REGEX.match(mac):
            flash(f"O MAC '{mac}' possui formato inválido.", "danger")
            return redirect(url_for("ramais.detalhe", ramal_id=ramal_id))

        # Checar duplicidade de IP em outro ramal ativo
        if ip:
            dup_ip = session_db.query(Ramal).filter(Ramal.ip == ip, Ramal.id != ramal_id, Ramal.ativo == True).first()
            if dup_ip:
                flash(f"O IP {ip} já pertence ao ramal '{dup_ip.descricao}'.", "warning")
                return redirect(url_for("ramais.detalhe", ramal_id=ramal_id))

        # Checar duplicidade de MAC
        if mac:
            dup_mac = session_db.query(Ramal).filter(Ramal.mac_cisco == mac, Ramal.id != ramal_id, Ramal.ativo == True).first()
            if dup_mac:
                flash(f"O MAC {mac} já pertence ao ramal '{dup_mac.descricao}'.", "warning")
                return redirect(url_for("ramais.detalhe", ramal_id=ramal_id))

        # Backup preventivo
        backup_mgr.criar_backup(motivo="pre_editar_ramal", usuario_id=session.get("usuario_id"))

        alteracoes = {}
        if ramal.ip != (ip or None):
            alteracoes["ip"] = {"anterior": ramal.ip, "novo": ip}
            ramal.ip = ip or None

        if ramal.mac_cisco != (mac or None):
            alteracoes["mac_cisco"] = {"anterior": ramal.mac_cisco, "novo": mac}
            ramal.mac_cisco = mac or None

        ramal.observacoes = observacoes or None

        # Campos adicionais para Administrador
        if is_admin:
            desc = request.form.get("descricao", "").strip()
            bloco = request.form.get("bloco", "").strip()
            modelo = request.form.get("modelo", "").strip()
            setor = request.form.get("setor", "").strip()
            localizacao = request.form.get("localizacao", "").strip()
            criticidade = request.form.get("criticidade", "NORMAL").upper()

            if desc and ramal.descricao != desc:
                alteracoes["descricao"] = {"anterior": ramal.descricao, "novo": desc}
                ramal.descricao = desc
            if bloco and ramal.bloco != bloco:
                alteracoes["bloco"] = {"anterior": ramal.bloco, "novo": bloco}
                ramal.bloco = bloco
            if modelo:
                ramal.modelo = modelo
            ramal.setor = setor or None
            ramal.localizacao = localizacao or None
            if criticidade in ("NORMAL", "ALTA", "CRITICA"):
                ramal.criticidade = criticidade

        ramal.atualizado_em = datetime.utcnow()

    registrar_auditoria(
        acao="EDITAR_RAMAL",
        entidade="ramal",
        entidade_id=ramal_id,
        detalhes=alteracoes,
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash("Dados do ramal atualizados com sucesso.", "success")
    return redirect(url_for("ramais.detalhe", ramal_id=ramal_id))


@ramais_bp.route("/<int:ramal_id>/toggle-ativo", methods=["POST"])
@admin_required
def toggle_ativo(ramal_id: int):
    """Desativa ou reativa o ramal."""
    backup_mgr.criar_backup(motivo="pre_toggle_ramal", usuario_id=session.get("usuario_id"))

    with db.session_scope() as session_db:
        ramal = session_db.query(Ramal).filter(Ramal.id == ramal_id).first()
        if not ramal:
            flash("Ramal não encontrado.", "danger")
            return redirect(url_for("ramais.lista"))

        ramal.ativo = not ramal.ativo
        novo_estado = "REATIVADO" if ramal.ativo else "DESATIVADO"
        if not ramal.ativo:
            ramal.status_atual = "INATIVO"

    registrar_auditoria(
        acao=f"RAMAL_{novo_estado}",
        entidade="ramal",
        entidade_id=ramal_id,
        detalhes={"novo_ativo": ramal.ativo},
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash(f"Ramal {novo_estado.lower()} com sucesso.", "info")
    return redirect(url_for("ramais.detalhe", ramal_id=ramal_id))


@ramais_bp.route("/<int:ramal_id>/excluir", methods=["POST"])
@admin_required
def excluir(ramal_id: int):
    """Exclusão definitiva com confirmação e auditoria obrigatória."""
    confirmacao = request.form.get("confirmacao", "").strip().upper()
    if confirmacao != "EXCLUIR":
        flash("Para excluir definitivamente, você deve digitar 'EXCLUIR' no campo de confirmação.", "warning")
        return redirect(url_for("ramais.detalhe", ramal_id=ramal_id))

    backup_mgr.criar_backup(motivo="pre_excluir_ramal", usuario_id=session.get("usuario_id"))

    with db.session_scope() as session_db:
        ramal = session_db.query(Ramal).filter(Ramal.id == ramal_id).first()
        if not ramal:
            flash("Ramal não encontrado.", "danger")
            return redirect(url_for("ramais.lista"))

        desc_removido = ramal.descricao
        dados_removidos = ramal.to_dict()
        session_db.delete(ramal)

    registrar_auditoria(
        acao="EXCLUSAO_DEFINITIVA_RAMAL",
        entidade="ramal",
        entidade_id=ramal_id,
        detalhes=dados_removidos,
        usuario_id=session.get("usuario_id"),
        ip_origem=request.remote_addr,
    )

    flash(f"Ramal '{desc_removido}' excluído definitivamente com registro em auditoria.", "success")
    return redirect(url_for("ramais.lista"))
