"""
Rotas para Importação, Diff Visual e Exportação de JSON Legado.
Compatível com a estrutura de blocos e campos do HAOC VoIP Monitor original.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response, session

from haoc_voip.web.app import login_required, admin_required, analista_ou_admin_required
from haoc_voip.core.importer import JSONImporter, exportar_para_json_legado

logger = logging.getLogger("haoc.routes.importacao")
importacao_bp = Blueprint("importacao", __name__)


@importacao_bp.route("/")
@login_required
def index():
    """Tela de upload e importação de arquivo JSON legado."""
    return render_template("importacao.html")


@importacao_bp.route("/analisar", methods=["POST"])
@admin_required
def analisar():
    """
    Recebe o arquivo JSON enviado pelo usuário, valida a estrutura,
    identifica inconsistências e calcula o diff completo contra a base SQLite.
    """
    if "arquivo" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

    file = request.files["arquivo"]
    if file.filename == "":
        return jsonify({"erro": "Arquivo não selecionado."}), 400

    try:
        content = file.read().decode("utf-8")
        importer = JSONImporter(content)
        analise = importer.validar_e_analisar()

        # Armazena temporariamente na sessão para aplicação subsequente
        session["temp_import_data"] = content

        return jsonify({"sucesso": True, "analise": analise})

    except json.JSONDecodeError as exc:
        return jsonify({"erro": f"Arquivo JSON corrompido ou mal formatado: {str(exc)}"}), 400
    except Exception as exc:
        logger.error("Erro ao analisar arquivo JSON: %s", exc)
        return jsonify({"erro": f"Falha na validação do JSON: {str(exc)}"}), 400


@importacao_bp.route("/aplicar", methods=["POST"])
@admin_required
def aplicar():
    """
    Aplica as alterações confirmadas pelo usuário (em lote ou seletivas)
    após backup automático preventivo.
    """
    raw_content = session.get("temp_import_data")
    if not raw_content:
        return jsonify({"erro": "Dados de importação expirados da sessão. Por favor, envie o arquivo novamente."}), 400

    req_data = request.get_json() or {}
    itens_selecionados = req_data.get("itens_selecionados")  # Lista de chaves ou None para todos
    remover_ausentes = bool(req_data.get("remover_ausentes", False))
    usuario_id = session.get("usuario_id")

    try:
        importer = JSONImporter(raw_content)
        resultado = importer.aplicar_alteracoes(
            itens_selecionados=itens_selecionados,
            remover_ausentes=remover_ausentes,
            usuario_id=usuario_id,
        )

        # Limpar da sessão
        session.pop("temp_import_data", None)

        return jsonify({
            "sucesso": True,
            "resultado": resultado,
            "mensagem": (
                f"Importação concluída com sucesso! "
                f"Inseridos: {resultado['inseridos']} | Atualizados: {resultado['atualizados']} | Removidos: {resultado['removidos']}"
            ),
        })

    except Exception as exc:
        logger.critical("Erro ao aplicar alterações do JSON: %s", exc)
        return jsonify({"erro": f"Falha ao persistir importação: {str(exc)}"}), 500


@importacao_bp.route("/exportar")
@analista_ou_admin_required
def exportar():
    """
    Exporta todo o cadastro ativo para o formato JSON tradicional estruturado por blocos.
    Compatível com versões legadas e backups externos.
    """
    try:
        dados_json = exportar_para_json_legado()
        json_str = json.dumps(dados_json, ensure_ascii=False, indent=2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return Response(
            json_str,
            mimetype="application/json; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=cadastro_ramais_haoc_{timestamp}.json"},
        )
    except Exception as exc:
        logger.error("Erro ao exportar JSON legado: %s", exc)
        flash(f"Falha ao gerar exportação JSON: {str(exc)}", "danger")
        return redirect(url_for("importacao.index"))
