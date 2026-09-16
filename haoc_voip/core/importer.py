"""
Módulo de Importação, Comparação (Diff) e Exportação de JSON Legado do HAOC.
Garante compatibilidade total com a estrutura organizada por blocos:
{
  "BLOCO A": [
    {"Modelo": "Cisco 7821", "I.P Cisco": "192.168.1.10", "Descrição": "1001 - Recepção", "I.P": "..."}
  ]
}
"""
from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

from haoc_voip.core.models import Ramal, Bloco, Setor
from haoc_voip.core.database import db
from haoc_voip.core.backup import backup_mgr
from haoc_voip.core.audit import registrar_auditoria

logger = logging.getLogger("haoc.importer")

# Padrões regex para validação estrita
IPV4_REGEX = re.compile(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$")
MAC_CISCO_REGEX = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|"  # 00:1B:54:12:34:56 ou 00-1B-54-12-34-56
    r"^([0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})$|"  # 001b.5412.3456 (formato Cisco)
    r"^([0-9A-Fa-f]{12})$"  # 001B54123456
)


def normalizar_mac(mac: str | None) -> str:
    """Normaliza o endereço MAC para formato padrão com dois pontos (00:1B:54:12:34:56)."""
    if not mac:
        return ""
    clean = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    if len(clean) == 12:
        return ":".join(clean[i:i+2] for i in range(0, 12, 2))
    return mac.strip().upper()


def validar_ipv4(ip: str | None) -> bool:
    """Valida se a string é um endereço IPv4 válido."""
    if not ip or not isinstance(ip, str):
        return False
    ip_clean = ip.strip()
    if not IPV4_REGEX.match(ip_clean):
        return False
    parts = ip_clean.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def extrair_numero_ramal(descricao: str) -> str:
    """Extrai número de ramal provável no início da descrição (ex: '1001 - Recepção' -> '1001')."""
    match = re.search(r"^\s*(\d{3,5})\b", descricao or "")
    if match:
        return match.group(1)
    return ""


def gerar_identificador_estavel(item: Dict[str, Any], bloco: str) -> str:
    """
    Gera um identificador estável para o ramal no JSON.
    Não depende de MAC se este estiver vazio.
    Prioriza: (bloco + numero_ramal) ou MAC válido ou (bloco + descricao normalizada).
    """
    mac = normalizar_mac(item.get("mac_cisco") or item.get("MAC Cisco") or item.get("MAC"))
    desc = (item.get("descricao") or item.get("Descrição") or item.get("Descricao") or "").strip()
    num = extrair_numero_ramal(desc)

    if num:
        return f"{bloco.strip().upper()}::RAMAL_{num}"
    if mac and mac not in ("00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"):
        return f"MAC_{mac}"
    
    # Fallback seguro
    norm_desc = re.sub(r"\s+", " ", desc).upper()
    return f"{bloco.strip().upper()}::DESC_{norm_desc}"


class JSONImporter:
    """Motor de validação, cálculo de diff e aplicação de JSON legado."""

    def __init__(self, raw_data: str | bytes | dict):
        if isinstance(raw_data, (str, bytes)):
            self.data = json.loads(raw_data)
        else:
            self.data = raw_data

    def validar_e_analisar(self) -> Dict[str, Any]:
        """
        Analisa o JSON fornecido, detecta inconsistências, novos ramais,
        alterações de IP/MAC/descrição, remoções e duplicidades em relação ao banco atual.
        """
        if not isinstance(self.data, dict):
            raise ValueError("O formato raiz do JSON deve ser um dicionário de blocos.")

        inconsistencias = []
        ramais_normalizados = []
        chaves_vistas = set()
        ips_vistos = set()
        macs_vistos = set()

        for bloco_nome, lista_ramais in self.data.items():
            if not isinstance(lista_ramais, list):
                inconsistencias.append({
                    "bloco": bloco_nome,
                    "ramal": "-",
                    "tipo": "FORMATO_INVALIDO",
                    "mensagem": f"O bloco '{bloco_nome}' deve conter uma lista de ramais.",
                })
                continue

            for idx, raw_item in enumerate(lista_ramais):
                if not isinstance(raw_item, dict):
                    continue

                # Compatibilidade com chaves legadas e variações de acentuação
                modelo = raw_item.get("Modelo") or raw_item.get("modelo") or "Cisco Padrão"
                descricao = (
                    raw_item.get("Descrição")
                    or raw_item.get("Descricao")
                    or raw_item.get("descricao")
                    or raw_item.get("Descrio")
                    or ""
                ).strip()
                
                # Detecção inteligente e robusta de IP e MAC
                candidato_ip = (raw_item.get("I.P") or raw_item.get("IP") or raw_item.get("ip") or "").strip()
                candidato_cisco = (
                    raw_item.get("MAC Cisco")
                    or raw_item.get("I.P Cisco")
                    or raw_item.get("MAC")
                    or raw_item.get("mac_cisco")
                    or raw_item.get("mac")
                    or ""
                ).strip()

                if validar_ipv4(candidato_ip):
                    ip = candidato_ip
                    mac = normalizar_mac(candidato_cisco)
                elif validar_ipv4(candidato_cisco):
                    ip = candidato_cisco
                    mac = normalizar_mac(candidato_ip)
                else:
                    ip = candidato_ip or candidato_cisco
                    mac = normalizar_mac(candidato_cisco or candidato_ip)

                setor = (raw_item.get("Setor") or raw_item.get("setor") or "").strip()
                localizacao = (raw_item.get("Localização") or raw_item.get("localizacao") or "").strip()
                criticidade = (raw_item.get("Criticidade") or raw_item.get("criticidade") or "NORMAL").upper()

                chave_estavel = gerar_identificador_estavel(
                    {"mac_cisco": mac, "descricao": descricao}, bloco=bloco_nome
                )

                # Checagens de inconsistência
                if not descricao:
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": f"Item #{idx+1}",
                        "tipo": "DESCRICAO_AUSENTE",
                        "mensagem": "Ramal sem descrição informada.",
                    })

                if ip and not validar_ipv4(ip):
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao or f"Item #{idx+1}",
                        "tipo": "IP_INVALIDO",
                        "mensagem": f"Endereço IP '{ip}' não é um IPv4 válido.",
                    })

                if mac and not MAC_CISCO_REGEX.match(mac):
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao or f"Item #{idx+1}",
                        "tipo": "MAC_INVALIDO",
                        "mensagem": f"MAC Cisco '{mac}' possui formato incorreto.",
                    })

                if not mac:
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao or f"Item #{idx+1}",
                        "tipo": "MAC_AUSENTE",
                        "mensagem": "MAC ausente. Identificador gerado a partir do número/descrição.",
                    })

                # Detecção de duplicidade dentro do arquivo
                if chave_estavel in chaves_vistas:
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao,
                        "tipo": "DUPLICIDADE_CADASTRO",
                        "mensagem": f"Ramal duplicado no arquivo: {chave_estavel}",
                    })
                chaves_vistas.add(chave_estavel)

                if ip and ip in ips_vistos:
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao,
                        "tipo": "IP_DUPLICADO",
                        "mensagem": f"IP {ip} já atribuído a outro ramal no mesmo arquivo.",
                    })
                if ip:
                    ips_vistos.add(ip)

                if mac and mac in macs_vistos:
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao,
                        "tipo": "MAC_DUPLICADO",
                        "mensagem": f"MAC {mac} já utilizado em outro registro no arquivo.",
                    })
                if mac:
                    macs_vistos.add(mac)

                ramais_normalizados.append({
                    "chave_estavel": chave_estavel,
                    "bloco": bloco_nome.strip(),
                    "modelo": modelo,
                    "descricao": descricao,
                    "ip": ip,
                    "mac_cisco": mac,
                    "setor": setor,
                    "localizacao": localizacao,
                    "criticidade": criticidade if criticidade in ("NORMAL", "ALTA", "CRITICA") else "NORMAL",
                })

        # Comparação com o banco de dados atual (Diff)
        with db.session_scope() as session:
            ramais_db = session.query(Ramal).filter(Ramal.ativo == True).all()
            db_map: Dict[str, Ramal] = {}
            for r in ramais_db:
                k = gerar_identificador_estavel({"mac_cisco": r.mac_cisco, "descricao": r.descricao}, bloco=r.bloco)
                db_map[k] = r

        novos = []
        alterados = []
        removidos = []
        iguais = []

        json_chaves = set()

        for item in ramais_normalizados:
            k = item["chave_estavel"]
            json_chaves.add(k)
            if k not in db_map:
                novos.append(item)
            else:
                existente = db_map[k]
                mudancas = {}
                if item["ip"] != (existente.ip or ""):
                    mudancas["ip"] = {"anterior": existente.ip, "novo": item["ip"]}
                if item["mac_cisco"] != (existente.mac_cisco or ""):
                    mudancas["mac_cisco"] = {"anterior": existente.mac_cisco, "novo": item["mac_cisco"]}
                if item["descricao"] != existente.descricao:
                    mudancas["descricao"] = {"anterior": existente.descricao, "novo": item["descricao"]}
                if item["modelo"] != (existente.modelo or ""):
                    mudancas["modelo"] = {"anterior": existente.modelo, "novo": item["modelo"]}
                if item["bloco"] != existente.bloco:
                    mudancas["bloco"] = {"anterior": existente.bloco, "novo": item["bloco"]}

                if mudancas:
                    item_alt = dict(item)
                    item_alt["ramal_id"] = existente.id
                    item_alt["mudancas"] = mudancas
                    alterados.append(item_alt)
                else:
                    iguais.append(item)

        # Ramais no banco que pertenciam aos blocos importados mas não estão mais no JSON
        blocos_importados = set(self.data.keys())
        for k, existente in db_map.items():
            if existente.bloco in blocos_importados and k not in json_chaves:
                removidos.append(existente.to_dict())

        return {
            "total_importado": len(ramais_normalizados),
            "total_novos": len(novos),
            "total_alterados": len(alterados),
            "total_removidos": len(removidos),
            "total_iguais": len(iguais),
            "inconsistencias": inconsistencias,
            "novos": novos,
            "alterados": alterados,
            "removidos": removidos,
        }

    def aplicar_alteracoes(
        self,
        itens_selecionados: List[Dict[str, Any]] | None = None,
        remover_ausentes: bool = False,
        usuario_id: int | None = None,
    ) -> Dict[str, int]:
        """
        Aplica as alterações no banco com backup prévio automático e auditoria completa.
        Suporta aplicação em lote total ou seletiva.
        """
        # 1. Backup obrigatório antes de alterações
        backup_mgr.criar_backup(motivo="pre_importacao_json", usuario_id=usuario_id)

        analise = self.validar_e_analisar()
        novos = analise["novos"]
        alterados = analise["alterados"]
        removidos = analise["removidos"]

        # Se houver filtro seletivo
        if itens_selecionados is not None:
            chaves_selecionadas = {it.get("chave_estavel") for it in itens_selecionados if it.get("chave_estavel")}
            novos = [n for n in novos if n["chave_estavel"] in chaves_selecionadas]
            alterados = [a for a in alterados if a["chave_estavel"] in chaves_selecionadas]

        inseridos_count = 0
        atualizados_count = 0
        removidos_count = 0

        with db.session_scope() as session:
            # Garantir existência de blocos
            todos_blocos = set(n["bloco"] for n in novos).union(a["bloco"] for a in alterados)
            for nome_bloco in todos_blocos:
                bloco_obj = session.query(Bloco).filter(Bloco.nome == nome_bloco).first()
                if not bloco_obj:
                    bloco_obj = Bloco(nome=nome_bloco, ativo=True)
                    session.add(bloco_obj)
            session.flush()

            # Processar novos
            for item in novos:
                bloco_obj = session.query(Bloco).filter(Bloco.nome == item["bloco"]).first()
                novo_ramal = Ramal(
                    modelo=item["modelo"],
                    mac_cisco=item["mac_cisco"] or None,
                    descricao=item["descricao"],
                    ip=item["ip"] or None,
                    bloco=item["bloco"],
                    bloco_id=bloco_obj.id if bloco_obj else None,
                    setor=item.get("setor") or None,
                    localizacao=item.get("localizacao") or None,
                    criticidade=item.get("criticidade", "NORMAL"),
                    ativo=True,
                )
                session.add(novo_ramal)
                inseridos_count += 1

            # Processar alterados
            for item in alterados:
                ramal_db = session.query(Ramal).filter(Ramal.id == item["ramal_id"]).first()
                if ramal_db:
                    mudancas = item.get("mudancas", {})
                    if "ip" in mudancas:
                        ramal_db.ip = item["ip"] or None
                    if "mac_cisco" in mudancas:
                        ramal_db.mac_cisco = item["mac_cisco"] or None
                    if "descricao" in mudancas:
                        ramal_db.descricao = item["descricao"]
                    if "modelo" in mudancas:
                        ramal_db.modelo = item["modelo"]
                    if "bloco" in mudancas:
                        ramal_db.bloco = item["bloco"]
                        bloco_obj = session.query(Bloco).filter(Bloco.nome == item["bloco"]).first()
                        if bloco_obj:
                            ramal_db.bloco_id = bloco_obj.id
                    ramal_db.atualizado_em = datetime.utcnow()
                    atualizados_count += 1

            # Remover se solicitado
            if remover_ausentes:
                for rem in removidos:
                    ramal_del = session.query(Ramal).filter(Ramal.id == rem["id"]).first()
                    if ramal_del:
                        ramal_del.ativo = False  # Desativação lógica segura
                        removidos_count += 1

        registrar_auditoria(
            acao="IMPORTACAO_JSON",
            entidade="importacao",
            detalhes={
                "inseridos": inseridos_count,
                "atualizados": atualizados_count,
                "removidos": removidos_count,
            },
            usuario_id=usuario_id,
        )

        return {
            "inseridos": inseridos_count,
            "atualizados": atualizados_count,
            "removidos": removidos_count,
        }


def exportar_para_json_legado() -> Dict[str, List[Dict[str, Any]]]:
    """
    Exporta todo o cadastro ativo para o formato JSON tradicional estruturado por blocos.
    Compatível com o formato legado esperado pelo HAOC VoIP Monitor.
    """
    export_dict: Dict[str, List[Dict[str, Any]]] = {}

    with db.session_scope() as session:
        ramais = session.query(Ramal).filter(Ramal.ativo == True).order_by(Ramal.bloco, Ramal.descricao).all()
        for r in ramais:
            bloco_nome = r.bloco or "GERAL"
            if bloco_nome not in export_dict:
                export_dict[bloco_nome] = []

            export_dict[bloco_nome].append({
                "Modelo": r.modelo or "Cisco Padrão",
                "I.P Cisco": r.ip or "",
                "Descrição": r.descricao,
                "I.P": r.ip or "",
                "MAC Cisco": r.mac_cisco or "",
                "Setor": r.setor or "",
                "Localização": r.localizacao or "",
                "Criticidade": r.criticidade,
            })

    return export_dict
