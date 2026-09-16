"""
Testes de Backup Automático e Restauração SQLite.
"""
from pathlib import Path
from haoc_voip.core.backup import backup_mgr


def test_backup_creation_and_listing():
    caminho = backup_mgr.criar_backup(motivo="teste_unitario")
    assert caminho is not None
    assert Path(caminho).exists()

    lista = backup_mgr.listar_backups()
    assert len(lista) >= 1
    assert any(b["nome"] == Path(caminho).name for b in lista)


def test_backup_restore_safety():
    # Criar um backup prévio
    caminho = backup_mgr.criar_backup(motivo="pre_restore_test")
    assert caminho is not None

    # Restaurar
    nome_arquivo = Path(caminho).name
    sucesso_rst = backup_mgr.restaurar_backup(nome_arquivo)
    assert sucesso_rst is True
