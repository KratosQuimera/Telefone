"""
Módulo de Backup Seguro e Restauração com Retenção Configurável.
Utiliza a API oficial de backup online do SQLite para consistência transacional absoluta.
"""
from __future__ import annotations

import logging
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from haoc_voip.config import Config
from haoc_voip.core.audit import registrar_auditoria

logger = logging.getLogger("haoc.backup")


class BackupManager:
    """Gerenciador de snapshots seguros e restauração do SQLite."""

    def __init__(self, db_path: Path | None = None, backup_dir: Path | None = None):
        self.db_path = Path(db_path or Config.DB_PATH)
        self.backup_dir = Path(backup_dir or Config.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def criar_backup(self, motivo: str = "auto", usuario_id: int | None = None) -> Path | None:
        """
        Cria snapshot consistente do banco de dados SQLite.
        Garante gravação atômica mesmo sob escrita concorrente usando a API conn.backup.
        Nome do backup com data, hora e segundos: backup_haoc_YYYYMMDD_HHMMSS.db
        """
        if not self.db_path.exists():
            logger.warning("Banco de dados %s ainda não existe. Backup ignorado.", self.db_path)
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_haoc_{timestamp}_{motivo}.db"
        dest_path = self.backup_dir / backup_filename
        temp_dest_path = self.backup_dir / f".tmp_{backup_filename}"

        try:
            # Conexão de origem (com timeout para concorrência)
            src_conn = sqlite3.connect(str(self.db_path), timeout=15)
            # Conexão de destino no arquivo temporário
            dst_conn = sqlite3.connect(str(temp_dest_path))
            
            # API nativa de backup do SQLite - cópia consistente bloco a bloco
            with dst_conn:
                src_conn.backup(dst_conn, pages=100, progress=None)
            
            dst_conn.close()
            src_conn.close()

            # Valida integridade do snapshot antes de renomear
            if not self.validar_integridade_arquivo(temp_dest_path):
                temp_dest_path.unlink(missing_ok=True)
                raise RuntimeError("Integridade do arquivo de backup temporário falhou.")

            # Renomeação atômica
            temp_dest_path.replace(dest_path)
            logger.info("Backup criado com sucesso: %s (motivo: %s)", dest_path.name, motivo)

            registrar_auditoria(
                acao="BACKUP_CRIADO",
                entidade="backup",
                entidade_id=dest_path.name,
                detalhes={"motivo": motivo, "caminho": str(dest_path), "tamanho_bytes": dest_path.stat().st_size},
                usuario_id=usuario_id,
            )

            # Limpar backups antigos de acordo com a política de retenção
            self.limpar_backups_antigos()

            return dest_path

        except Exception as exc:
            logger.critical("Falha grave na criação do backup do banco de dados: %s", exc)
            if temp_dest_path.exists():
                temp_dest_path.unlink(missing_ok=True)
            return None

    def validar_integridade_arquivo(self, file_path: Path) -> bool:
        """Verifica se o arquivo de banco SQLite é válido e íntegro."""
        if not file_path.exists() or file_path.stat().st_size == 0:
            return False
        try:
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            conn.close()
            return result is not None and result[0] == "ok"
        except Exception as exc:
            logger.error("Erro na checagem de integridade de %s: %s", file_path, exc)
            return False

    def restaurar_backup(self, backup_filename_ou_path: str | Path, usuario_id: int | None = None) -> bool:
        """
        Restaura com segurança uma cópia de backup.
        Antes de sobrescrever o banco atual, cria um backup de segurança preventivo.
        """
        path = Path(backup_filename_ou_path)
        if not path.is_absolute():
            path = self.backup_dir / path.name

        if not path.exists():
            logger.error("Arquivo de backup para restauração não encontrado: %s", path)
            return False

        if not self.validar_integridade_arquivo(path):
            logger.error("Arquivo de backup corrompido ou inválido: %s", path)
            return False

        # Criar backup preventivo antes de qualquer restauração
        self.criar_backup(motivo="pre_restauracao", usuario_id=usuario_id)

        try:
            # Backup do arquivo selecionado para o banco principal
            src_conn = sqlite3.connect(str(path))
            dst_conn = sqlite3.connect(str(self.db_path), timeout=30)
            
            with dst_conn:
                src_conn.backup(dst_conn)
                
            dst_conn.close()
            src_conn.close()

            # Valida integridade final do banco principal
            if not self.validar_integridade_arquivo(self.db_path):
                raise RuntimeError("Banco de dados principal apresentou falha de integridade após restauração.")

            logger.info("Restauração do backup %s concluída com sucesso.", path.name)
            registrar_auditoria(
                acao="BACKUP_RESTAURADO",
                entidade="backup",
                entidade_id=path.name,
                detalhes={"arquivo_origem": str(path)},
                usuario_id=usuario_id,
            )
            return True

        except Exception as exc:
            logger.critical("Falha catastrófica ao restaurar backup: %s", exc)
            return False

    def listar_backups(self) -> List[Dict[str, Any]]:
        """Retorna lista ordenada dos backups disponíveis."""
        backups = []
        if not self.backup_dir.exists():
            return backups

        for item in sorted(self.backup_dir.glob("backup_haoc_*.db"), reverse=True):
            if item.is_file():
                stat = item.stat()
                backups.append({
                    "nome": item.name,
                    "caminho": str(item),
                    "tamanho_kb": round(stat.st_size / 1024, 2),
                    "criado_em": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                    "timestamp": stat.st_mtime,
                })
        return backups

    def limpar_backups_antigos(self) -> int:
        """Remove backups que excedam os dias de retenção ou a contagem máxima."""
        removidos = 0
        backups = self.listar_backups()
        limite_data = datetime.now() - timedelta(days=Config.BACKUP_RETENTION_DAYS)

        # 1. Limpeza por dias de retenção
        for bkp in backups:
            dt = datetime.fromtimestamp(bkp["timestamp"])
            if dt < limite_data:
                try:
                    Path(bkp["caminho"]).unlink(missing_ok=True)
                    removidos += 1
                except Exception as e:
                    logger.warning("Erro ao remover backup expirado %s: %s", bkp["nome"], e)

        # 2. Limpeza por quantidade máxima
        restantes = self.listar_backups()
        if len(restantes) > Config.MAX_BACKUPS_COUNT:
            excedentes = restantes[Config.MAX_BACKUPS_COUNT:]
            for bkp in excedentes:
                try:
                    Path(bkp["caminho"]).unlink(missing_ok=True)
                    removidos += 1
                except Exception as e:
                    logger.warning("Erro ao remover backup excedente %s: %s", bkp["nome"], e)

        return removidos


backup_mgr = BackupManager()
