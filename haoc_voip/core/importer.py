"""
Módulo de Importação, Comparação (Diff) e Exportação de JSON do HAOC VoIP Monitor.
Compatibilidade nativa com o formato organizado por blocos:
{
  "Bloco A": [
    { "Modelo": "Cisco Unified Client Services Framework", "I.P Cisco": "CSF18982", "Descrição": "JABBER - Recp_Bl.A - Ouvidoria - 6452", "I.P": "None" },
    { "Modelo": "Cisco 7841", "I.P Cisco": "SEP2C86D276454B", "Descrição": "Matriz - 1A Bl.A - Juridico - 0351", "I.P": "10.192.58.24" }
  ],
  "Bloco B": [ ... ]
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

IPV4_REGEX = re.compile(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$")
MAC_CISCO_REGEX = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|"          # 00:1B:54:12:34:56
    r"^([0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})$|"  # 001b.5412.3456
    r"^([0-9A-Fa-f]{12})$"                                   # 001B54123456
)


def normalizar_mac(mac: str | None) -> str:
    """Normaliza o endereço MAC para formato padrão com dois pontos (00:1B:54:12:34:56) ou preserva CSF."""
    if not mac:
        return ""
    mac_strip = mac.strip()
    if mac_strip.upper().startswith("CSF"):
        return mac_strip.upper()
    if mac_strip.upper().startswith("SEP") and len(mac_strip) == 15:
        mac_strip = mac_strip[3:]
    clean = re.sub(r"[^0-9A-Fa-f]", "", mac_strip).upper()
    if len(clean) == 12:
        return ":".join(clean[i:i+2] for i in range(0, 12, 2))
    return mac_strip.upper()


def formatar_cisco_id(mac_ou_id: str | None) -> str:
    """Converte MAC normalizado para notação SEP Cisco (ex: SEP2C86D276454B) ou preserva CSF."""
    if not mac_ou_id:
        return ""
    mac_strip = mac_ou_id.strip().upper()
    if mac_strip.startswith("CSF"):
        return mac_strip
    clean = re.sub(r"[^0-9A-Fa-f]", "", mac_strip)
    if len(clean) == 12:
        return f"SEP{clean}"
    return mac_strip


def validar_ipv4(ip: str | None) -> bool:
    """Valida se a string é um endereço IPv4 válido."""
    if not ip or not isinstance(ip, str):
        return False
    ip_clean = ip.strip()
    if ip_clean.lower() in ("none", "null", "-", ""):
        return False
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
    """
    Extrai o número do ramal a partir da descrição.
    Suporta sufixo (ex: 'Matriz - 1A Bl.A - Juridico - 0351' -> '0351')
    e prefixo (ex: '1001 - Recepção' -> '1001').
    """
    if not descricao:
        return ""
    # 1. Tentar número no final após traço (padrão HAOC CUCM)
    match_fim = re.search(r"(?:-\s*|\b)(\d{3,5})\s*$", descricao)
    if match_fim:
        return match_fim.group(1)

    # 2. Tentar número no início
    match_ini = re.search(r"^\s*(\d{3,5})\b", descricao)
    if match_ini:
        return match_ini.group(1)

    # 3. Qualquer número isolado de 3 a 5 dígitos
    match_qualquer = re.search(r"\b(\d{3,5})\b", descricao)
    if match_qualquer:
        return match_qualquer.group(1)

    return ""


def extrair_setor_descricao(descricao: str) -> str:
    """Extrai setor aproximado da descrição com formato de múltiplos traços."""
    if not descricao:
        return "Geral"
    partes = [p.strip() for p in descricao.split(" - ") if p.strip()]
    if len(partes) >= 3:
        # Penúltima parte costuma ser o setor/quarto
        penultima = partes[-2]
        # Se for apenas o número repetido, pegar a antepenúltima
        if re.match(r"^\d+$", penultima) and len(partes) >= 4:
            return partes[-3]
        return penultima
    elif len(partes) == 2:
        return partes[1] if not re.match(r"^\d+$", partes[1]) else partes[0]
    return "Geral"


def gerar_identificador_estavel(item: Dict[str, Any], bloco: str) -> str:
    """
    Gera um identificador estável para o ramal no JSON.
    Prioriza: (bloco + numero_ramal) ou MAC Cisco normalizado ou (bloco + descricao).
    """
    mac = normalizar_mac(item.get("mac_cisco") or item.get("I.P Cisco") or item.get("MAC Cisco") or item.get("MAC"))
    desc = (item.get("descricao") or item.get("Descrição") or item.get("Descricao") or "").strip()
    num = item.get("numero") or extrair_numero_ramal(desc)

    if num:
        return f"{bloco.strip().upper()}::RAMAL_{num}"
    if mac and mac not in ("00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"):
        return f"MAC_{mac}"

    norm_desc = re.sub(r"\s+", " ", desc).upper()
    return f"{bloco.strip().upper()}::DESC_{norm_desc}"


class JSONImporter:
    """Motor de validação, cálculo de diff e aplicação de JSON do HAOC."""

    def __init__(self, raw_data: str | bytes | dict):
        if isinstance(raw_data, (str, bytes)):
            self.data = json.loads(raw_data)
        else:
            self.data = raw_data

    def validar_e_analisar(self) -> Dict[str, Any]:
        """
        Analisa o JSON fornecido (formato por blocos ou lista plana),
        detecta inconsistências, novos ramais, alterações e duplicidades.
        """
        if not isinstance(self.data, dict) and not isinstance(self.data, list):
            raise ValueError("O formato do JSON deve ser um objeto estruturado por blocos ou uma lista de ramais.")

        # Se for lista plana, agrupar sob "Geral" ou bloco do item
        data_blocos: Dict[str, List[Dict[str, Any]]] = {}
        if isinstance(self.data, list):
            for it in self.data:
                blk = (it.get("bloco") or it.get("Bloco") or "Geral").strip()
                data_blocos.setdefault(blk, []).append(it)
        else:
            data_blocos = self.data

        inconsistencias = []
        ramais_normalizados = []
        chaves_vistas = set()
        ips_vistos = set()
        macs_vistos = set()

        for bloco_nome, lista_ramais in data_blocos.items():
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

                modelo = raw_item.get("Modelo") or raw_item.get("modelo") or "Cisco 7841"
                descricao = (
                    raw_item.get("Descrição")
                    or raw_item.get("Descricao")
                    or raw_item.get("descricao")
                    or ""
                ).strip()

                # IP Cisco (SEP... ou CSF...) e IP de rede
                raw_cisco = (
                    raw_item.get("I.P Cisco")
                    or raw_item.get("MAC Cisco")
                    or raw_item.get("mac_cisco")
                    or raw_item.get("mac")
                    or ""
                ).strip()

                raw_ip = (
                    raw_item.get("I.P")
                    or raw_item.get("IP")
                    or raw_item.get("ip")
                    or ""
                ).strip()

                # Tratar "None" / "null" / "-" como sem IP (Status Offline)
                if raw_ip.lower() in ("none", "null", "-", ""):
                    ip = ""
                else:
                    ip = raw_ip

                mac = normalizar_mac(raw_cisco)

                # Extrair número e setor
                numero = raw_item.get("numero") or extrair_numero_ramal(descricao)
                setor = (raw_item.get("Setor") or raw_item.get("setor") or "").strip()
                if not setor:
                    setor = extrair_setor_descricao(descricao)

                criticidade = (raw_item.get("Criticidade") or raw_item.get("criticidade") or "NORMAL").upper()

                chave_estavel = gerar_identificador_estavel(
                    {"mac_cisco": mac, "descricao": descricao, "numero": numero}, bloco=bloco_nome
                )

                # Validações e avisos suaves
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

                # Duplicidade
                if chave_estavel in chaves_vistas:
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao or f"Ramal {numero}",
                        "tipo": "DUPLICIDADE_CADASTRO",
                        "mensagem": f"Ramal duplicado no arquivo: {chave_estavel}",
                    })
                chaves_vistas.add(chave_estavel)

                if ip and ip in ips_vistos:
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao or f"Ramal {numero}",
                        "tipo": "IP_DUPLICADO",
                        "mensagem": f"IP {ip} já atribuído a outro ramal no mesmo arquivo.",
                    })
                if ip:
                    ips_vistos.add(ip)

                if mac and mac in macs_vistos and not mac.startswith("CSF"):
                    inconsistencias.append({
                        "bloco": bloco_nome,
                        "ramal": descricao or f"Ramal {numero}",
                        "tipo": "MAC_DUPLICADO",
                        "mensagem": f"MAC {mac} já utilizado em outro registro no arquivo.",
                    })
                if mac and not mac.startswith("CSF"):
                    macs_vistos.add(mac)

                status_calc = "ONLINE" if ip else "OFFLINE"

                ramais_normalizados.append({
                    "chave_estavel": chave_estavel,
                    "bloco": bloco_nome.strip(),
                    "modelo": modelo,
                    "numero": numero,
                    "descricao": descricao,
                    "ip": ip,
                    "mac_cisco": mac,
                    "cisco_id": raw_cisco or formatar_cisco_id(mac),
                    "setor": setor,
                    "criticidade": criticidade if criticidade in ("NORMAL", "ALTA", "CRITICA") else "NORMAL",
                    "status": status_calc,
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

        blocos_importados = set(data_blocos.keys())
        for k, existente in db_map.items():
            if existente.bloco in blocos_importados and k not in json_chaves:
                removidos.append(existente.to_dict())

        return {
            "total_importado": len(ramais_normalizados),
            "total_novos": len(novos),
            "total_alterados": len(alterados),
            "total_removidos": len(removidos),
            "total_iguais": len(iguais),
            "estatisticas": {
                "total_no_arquivo": len(ramais_normalizados),
                "novos": len(novos),
                "alterados": len(alterados),
                "removidos": len(removidos),
            },
            "inconsistencias": inconsistencias,
            "novos": novos,
            "alterados": alterados,
            "removidos": removidos,
            "ramais_normalizados": ramais_normalizados,
        }

    def aplicar_alteracoes(
        self,
        itens_selecionados: List[Dict[str, Any]] | None = None,
        remover_ausentes: bool = False,
        usuario_id: int | None = None,
    ) -> Dict[str, int]:
        """Aplica alterações no banco SQLite com backup automático e auditoria."""
        backup_mgr.criar_backup(motivo="pre_importacao_json", usuario_id=usuario_id)

        analise = self.validar_e_analisar()
        novos = analise["novos"]
        alterados = analise["alterados"]
        removidos = analise["removidos"]

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
                is_on = bool(item["ip"])
                novo_ramal = Ramal(
                    modelo=item["modelo"],
                    mac_cisco=item["mac_cisco"] or item.get("cisco_id") or None,
                    descricao=item["descricao"],
                    ip=item["ip"] or None,
                    bloco=item["bloco"],
                    bloco_id=bloco_obj.id if bloco_obj else None,
                    setor=item.get("setor") or None,
                    criticidade=item.get("criticidade", "NORMAL"),
                    status_atual="ONLINE" if is_on else "OFFLINE",
                    ultima_latencia=12.0 if is_on else None,
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
                        ramal_db.status_atual = "ONLINE" if item["ip"] else "OFFLINE"
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

            if remover_ausentes:
                for rem in removidos:
                    ramal_del = session.query(Ramal).filter(Ramal.id == rem["id"]).first()
                    if ramal_del:
                        ramal_del.ativo = False
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
            "desativados": removidos_count,
            "removidos": removidos_count,
        }


def exportar_para_json_legado() -> Dict[str, List[Dict[str, Any]]]:
    """
    Exporta todo o cadastro ativo para o modelo estruturado por blocos do HAOC:
    {
      "Bloco A": [
        {
          "Modelo": "Cisco 7841",
          "I.P Cisco": "SEP2C86D276454B",
          "Descrição": "Matriz - 1A Bl.A - Juridico - 0351",
          "I.P": "10.192.58.24"
        }
      ]
    }
    """
    export_dict: Dict[str, List[Dict[str, Any]]] = {}

    with db.session_scope() as session:
        ramais = session.query(Ramal).filter(Ramal.ativo == True).order_by(Ramal.bloco, Ramal.descricao).all()
        for r in ramais:
            bloco_nome = r.bloco or "Bloco Central"
            if bloco_nome not in export_dict:
                export_dict[bloco_nome] = []

            # Montar identificador Cisco (SEP<MAC> ou CSF ou original)
            cisco_id = formatar_cisco_id(r.mac_cisco)

            export_dict[bloco_nome].append({
                "Modelo": r.modelo or "Cisco 7841",
                "I.P Cisco": cisco_id,
                "Descrição": r.descricao,
                "I.P": r.ip if r.ip else "None",
            })

    return export_dict
