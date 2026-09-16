"""
Testes de Importação de JSON Legado e Comparação Estrutural (Diff).
"""
import json
import pytest
from haoc_voip.core.importer import JSONImporter
from haoc_voip.core.database import db
from haoc_voip.core.models import Ramal


def test_import_and_diff_detection():
    dados_legados = {
        "BLOCO TESTE A": [
            {
                "Descrição": "9001 - Balcão Teste",
                "I.P": "192.168.99.10",
                "I.P Cisco": "00:1B:54:99:10:01",
                "Modelo": "Cisco CP-7821"
            },
            {
                "Descrição": "9002 - Sala Médica Teste",
                "I.P": "192.168.99.20",
                "I.P Cisco": "00:1B:54:99:20:02",
                "Modelo": "Cisco CP-8841"
            }
        ]
    }

    importer = JSONImporter(json.dumps(dados_legados))
    analise = importer.validar_e_analisar()
    assert len(analise["novos"]) >= 2

    # Aplicação do lote
    res_aplicacao = importer.aplicar_alteracoes(
        itens_selecionados=analise["novos"],
        remover_ausentes=False
    )
    assert res_aplicacao["inseridos"] >= 2

    # Verificar se foram persistidos no banco SQLite
    with db.session_scope() as session:
        r1 = session.query(Ramal).filter(Ramal.descricao == "9001 - Balcão Teste").first()
        assert r1 is not None
        assert r1.ip == "192.168.99.10"
        assert r1.mac_cisco == "00:1B:54:99:10:01"
        assert r1.bloco == "BLOCO TESTE A"

    # Agora simular uma modificação de IP e modelo no mesmo JSON
    dados_modificados = {
        "BLOCO TESTE A": [
            {
                "Descrição": "9001 - Balcão Teste",
                "I.P": "192.168.99.15",          # IP alterado
                "I.P Cisco": "00:1B:54:99:10:01",
                "Modelo": "Cisco CP-8845"        # Modelo alterado
            }
        ]
    }

    importer2 = JSONImporter(dados_modificados)
    analise2 = importer2.validar_e_analisar()
    assert len(analise2["alterados"]) >= 1

    item_alt = next((d for d in analise2["alterados"] if d["descricao"] == "9001 - Balcão Teste"), None)
    assert item_alt is not None
    assert "ip" in item_alt["mudancas"]
    assert "modelo" in item_alt["mudancas"]


def test_invalid_json_format():
    with pytest.raises(Exception):
        JSONImporter("JSON QUEBRADO INVALIDO {")
