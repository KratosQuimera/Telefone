"""
Modelos SQLAlchemy para o HAOC VoIP Monitor Enterprise.
Define o esquema do banco de dados relacional (SQLite).
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class StatusRamal(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    INATIVO = "INATIVO"
    AGUARDANDO = "AGUARDANDO"


class PerfilUsuario(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    ANALISTA = "ANALISTA"
    VISUALIZACAO = "VISUALIZACAO"


class Bloco(Base):
    """Tabela de blocos hospitalares (ex: Bloco A, Bloco B, Pronto Socorro, UTI)."""
    __tablename__ = "blocos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), unique=True, nullable=False, index=True)
    cor = Column(String(20), default="#0284c7")  # Hex code para exibição no dashboard
    ativo = Column(Boolean, default=True, nullable=False)

    ramais = relationship("Ramal", back_populates="bloco_rel", cascade="all")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cor": self.cor,
            "ativo": self.ativo,
        }


class Setor(Base):
    """Tabela de setores hospitalares (ex: Recepção, UTI Geral, Farmácia Central)."""
    __tablename__ = "setores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(120), unique=True, nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)

    ramais = relationship("Ramal", back_populates="setor_rel")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "ativo": self.ativo,
        }


class Ramal(Base):
    """
    Tabela principal de ramais VoIP Cisco.
    Identificador único permanente e independente de alterações de IP ou MAC.
    """
    __tablename__ = "ramais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    modelo = Column(String(80), nullable=True)  # Ex: Cisco CP-7821, CP-8841
    mac_cisco = Column(String(30), nullable=True, index=True)  # Ex: 00:1B:54:12:34:56 ou 001B54123456
    descricao = Column(String(200), nullable=False, index=True)  # Ex: "1001 - Balcão Recepção A"
    ip = Column(String(45), nullable=True, index=True)  # Ex: 192.168.10.25
    bloco = Column(String(100), nullable=False, index=True)  # Bloco físico/lógico
    bloco_id = Column(Integer, ForeignKey("blocos.id", ondelete="SET NULL"), nullable=True)
    setor = Column(String(120), nullable=True, index=True)  # Nome do setor
    setor_id = Column(Integer, ForeignKey("setores.id", ondelete="SET NULL"), nullable=True)
    localizacao = Column(String(150), nullable=True)  # Localização detalhada (ex: 2º Andar, Sala 204)
    criticidade = Column(String(20), default="NORMAL", nullable=False)  # NORMAL, ALTA, CRITICA
    ativo = Column(Boolean, default=True, nullable=False, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Metadados operacionais do monitoramento
    status_atual = Column(String(20), default=StatusRamal.AGUARDANDO.value, nullable=False)
    ultima_latencia = Column(Float, nullable=True)  # Em milissegundos
    ultimo_visto_online = Column(DateTime, nullable=True)
    ultimo_visto_offline = Column(DateTime, nullable=True)
    ultima_verificacao = Column(DateTime, nullable=True)
    ultimo_erro = Column(String(255), nullable=True)
    observacoes = Column(Text, nullable=True)

    # Relacionamentos
    bloco_rel = relationship("Bloco", back_populates="ramais")
    setor_rel = relationship("Setor", back_populates="ramais")
    monitoramentos = relationship("Monitoramento", back_populates="ramal", cascade="all, delete-orphan")
    incidentes = relationship("Incidente", back_populates="ramal", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="ramal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ramal_status_bloco", "status_atual", "bloco"),
        Index("idx_ramal_ip", "ip"),
    )

    def to_dict(self):
        # Calcular duração da indisponibilidade em segundos
        offline_seconds = 0
        if self.status_atual == StatusRamal.OFFLINE.value and self.ultimo_visto_offline:
            offline_seconds = int((datetime.utcnow() - self.ultimo_visto_offline).total_seconds())

        return {
            "id": self.id,
            "modelo": self.modelo or "Cisco Padrão",
            "mac_cisco": self.mac_cisco or "",
            "descricao": self.descricao,
            "ip": self.ip or "",
            "bloco": self.bloco,
            "bloco_id": self.bloco_id,
            "setor": self.setor or "",
            "setor_id": self.setor_id,
            "localizacao": self.localizacao or "",
            "criticidade": self.criticidade,
            "ativo": self.ativo,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "status": self.status_atual,
            "latencia": round(self.ultima_latencia, 1) if self.ultima_latencia is not None else None,
            "ultima_verificacao": self.ultima_verificacao.strftime("%H:%M:%S %d/%m/%Y") if self.ultima_verificacao else None,
            "duracao_offline_segundos": offline_seconds,
            "duracao_offline_formatada": self._format_duration(offline_seconds) if offline_seconds > 0 else "-",
            "ultimo_erro": self.ultimo_erro,
            "observacoes": self.observacoes or "",
        }

    @staticmethod
    def _format_duration(seconds: int) -> str:
        if seconds <= 0:
            return "0s"
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        days, hours = divmod(hours, 24)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if mins > 0:
            parts.append(f"{mins}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        return " ".join(parts)


class Monitoramento(Base):
    """Registro histórico de varreduras de ping por ramal."""
    __tablename__ = "monitoramentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ramal_id = Column(Integer, ForeignKey("ramais.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    latencia = Column(Float, nullable=True)  # Latência em ms
    verificado_em = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    erro = Column(String(255), nullable=True)

    ramal = relationship("Ramal", back_populates="monitoramentos")

    def to_dict(self):
        return {
            "id": self.id,
            "ramal_id": self.ramal_id,
            "status": self.status,
            "latencia": round(self.latencia, 1) if self.latencia is not None else None,
            "verificado_em": self.verificado_em.strftime("%Y-%m-%d %H:%M:%S") if self.verificado_em else None,
            "erro": self.erro,
        }


class Incidente(Base):
    """
    Registro de incidentes de indisponibilidade (queda e retorno).
    Criado quando o ramal passa para OFFLINE e fechado com a duração quando retorna a ONLINE.
    """
    __tablename__ = "incidentes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ramal_id = Column(Integer, ForeignKey("ramais.id", ondelete="CASCADE"), nullable=False, index=True)
    iniciado_em = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    encerrado_em = Column(DateTime, nullable=True)
    duracao = Column(Integer, nullable=True)  # Duração em segundos
    ip_monitorado = Column(String(45), nullable=True)
    mac_cisco = Column(String(30), nullable=True)
    bloco = Column(String(100), nullable=True)
    status_anterior = Column(String(20), default=StatusRamal.ONLINE.value)
    novo_status = Column(String(20), default=StatusRamal.OFFLINE.value)
    latencia_final = Column(Float, nullable=True)
    causa = Column(String(150), default="Indisponibilidade de rede")
    observacao = Column(Text, nullable=True)

    ramal = relationship("Ramal", back_populates="incidentes")
    alertas = relationship("Alerta", back_populates="incidente")

    def to_dict(self):
        duracao_calc = self.duracao
        if duracao_calc is None and not self.encerrado_em:
            duracao_calc = int((datetime.utcnow() - self.iniciado_em).total_seconds())

        return {
            "id": self.id,
            "ramal_id": self.ramal_id,
            "ramal_descricao": self.ramal.descricao if self.ramal else "Ramal desconhecido",
            "iniciado_em": self.iniciado_em.strftime("%d/%m/%Y %H:%M:%S") if self.iniciado_em else None,
            "encerrado_em": self.encerrado_em.strftime("%d/%m/%Y %H:%M:%S") if self.encerrado_em else "Aberto",
            "duracao_segundos": duracao_calc,
            "duracao_formatada": Ramal._format_duration(duracao_calc) if duracao_calc else "-",
            "ip_monitorado": self.ip_monitorado or (self.ramal.ip if self.ramal else ""),
            "mac_cisco": self.mac_cisco or (self.ramal.mac_cisco if self.ramal else ""),
            "bloco": self.bloco or (self.ramal.bloco if self.ramal else ""),
            "status_anterior": self.status_anterior,
            "novo_status": self.novo_status,
            "latencia": round(self.latencia_final, 1) if self.latencia_final else None,
            "causa": self.causa or "Indisponibilidade de rede",
            "observacao": self.observacao or "",
            "aberto": self.encerrado_em is None,
        }


class Usuario(Base):
    """Tabela de usuários com perfis RBAC (ADMINISTRADOR, ANALISTA, VISUALIZACAO)."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(120), nullable=False)
    login = Column(String(60), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(30), default=PerfilUsuario.ANALISTA.value, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    tentativas_falhas = Column(Integer, default=0, nullable=False)
    bloqueado_ate = Column(DateTime, nullable=True)
    ultimo_login = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    auditorias = relationship("Auditoria", back_populates="usuario")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "login": self.login,
            "perfil": self.perfil,
            "ativo": self.ativo,
            "ultimo_login": self.ultimo_login.strftime("%d/%m/%Y %H:%M:%S") if self.ultimo_login else None,
            "criado_em": self.criado_em.strftime("%d/%m/%Y %H:%M") if self.criado_em else None,
        }


class Auditoria(Base):
    """Trilha de auditoria das operações realizadas no sistema."""
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    acao = Column(String(80), nullable=False)  # CRIAR, EDITAR, EXCLUIR, DESATIVAR, REATIVAR, IMPORTAR, RESTAURAR, LOGIN
    entidade = Column(String(60), nullable=False)  # ramal, usuario, configuracao, backup, importacao
    entidade_id = Column(String(60), nullable=True)
    detalhes = Column(Text, nullable=True)
    ip_origem = Column(String(45), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    usuario = relationship("Usuario", back_populates="auditorias")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_nome": self.usuario.nome if self.usuario else "Sistema",
            "usuario_login": self.usuario.login if self.usuario else "system",
            "acao": self.acao,
            "entidade": self.entidade,
            "entidade_id": self.entidade_id,
            "detalhes": self.detalhes,
            "ip_origem": self.ip_origem,
            "criado_em": self.criado_em.strftime("%d/%m/%Y %H:%M:%S") if self.criado_em else None,
        }


class Configuracao(Base):
    """Pares chave-valor para parâmetros operacionais do sistema."""
    __tablename__ = "configuracoes"

    chave = Column(String(80), primary_key=True)
    valor = Column(Text, nullable=True)
    descricao = Column(String(200), nullable=True)
    tipo = Column(String(20), default="string")  # string, int, float, bool, json
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "chave": self.chave,
            "valor": self.valor,
            "descricao": self.descricao,
            "tipo": self.tipo,
        }


class Alerta(Base):
    """Alertas operacionais do sistema com deduplicação por incidente."""
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ramal_id = Column(Integer, ForeignKey("ramais.id", ondelete="CASCADE"), nullable=False, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="SET NULL"), nullable=True, index=True)
    tipo = Column(String(30), default="QUEDA")  # QUEDA, RECUPERACAO, LATENCIA_ALTA, CRITICO
    mensagem = Column(String(255), nullable=False)
    lido = Column(Boolean, default=False, nullable=False)
    lido_em = Column(DateTime, nullable=True)
    lido_por = Column(String(100), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    ramal = relationship("Ramal", back_populates="alertas")
    incidente = relationship("Incidente", back_populates="alertas")

    def to_dict(self):
        return {
            "id": self.id,
            "ramal_id": self.ramal_id,
            "ramal_descricao": self.ramal.descricao if self.ramal else "Ramal",
            "bloco": self.ramal.bloco if self.ramal else "",
            "incidente_id": self.incidente_id,
            "tipo": self.tipo,
            "mensagem": self.mensagem,
            "lido": self.lido,
            "lido_em": self.lido_em.strftime("%d/%m/%Y %H:%M:%S") if self.lido_em else None,
            "criado_em": self.criado_em.strftime("%d/%m/%Y %H:%M:%S") if self.criado_em else None,
        }
