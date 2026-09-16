"""
Motor de Monitoramento de Rede Paralelo com ThreadPoolExecutor.
Executa varreduras de ping com controle de concorrência, cancelamento seguro,
máquina de estados para incidentes, detecção de latência e cálculo de disponibilidade.
"""
from __future__ import annotations

import logging
import platform
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

from haoc_voip.config import Config
from haoc_voip.core.models import Ramal, Monitoramento, Incidente, StatusRamal
from haoc_voip.core.database import db
from haoc_voip.core.importer import validar_ipv4
from haoc_voip.core.alerts import alert_mgr

logger = logging.getLogger("haoc.monitor")


def executar_ping(ip: str, timeout_seconds: float = 1.5, retries: int = 2) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Executa ping ICMP compatível tanto com Windows quanto com Linux.
    Retorna (sucesso: bool, latencia_ms: float | None, erro: str | None).
    """
    if not ip or not validar_ipv4(ip):
        return False, None, "IP inválido ou não configurado"

    is_win = platform.system().lower() == "windows"
    timeout_ms = int(timeout_seconds * 1000)

    # Argumentos do ping dependendo da plataforma
    if is_win:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        # No Linux, -c 1 (1 pacote), -W <timeout em segundos>
        timeout_arg = max(1, int(timeout_seconds))
        cmd = ["ping", "-c", "1", "-W", str(timeout_arg), ip]

    for tentativa in range(retries):
        try:
            inicio = time.perf_counter()
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds + 1.0,
            )
            fim = time.perf_counter()
            elapsed_ms = (fim - inicio) * 1000

            if proc.returncode == 0:
                # Tentar extrair tempo real do output se disponível
                latencia = elapsed_ms
                out = proc.stdout.lower()
                # Windows: 'tempo=12ms' ou 'time=12ms'
                # Linux: 'time=12.3 ms'
                for line in out.splitlines():
                    if "time=" in line or "tempo=" in line:
                        import re
                        m = re.search(r"(?:time|tempo)[=<]([0-9.]+)\s*ms", line)
                        if m:
                            try:
                                latencia = float(m.group(1))
                            except ValueError:
                                pass
                        break

                return True, max(0.5, round(latencia, 1)), None

        except subprocess.TimeoutExpired:
            pass
        except Exception as exc:
            logger.debug("Erro ao executar comando de ping para %s: %s", ip, exc)
            return False, None, f"Falha de monitoramento: {str(exc)}"

    return False, None, "Indisponibilidade de rede (Sem resposta ao ping)"


class MonitorEngine:
    """Motor de monitoramento periódico e assíncrono."""

    def __init__(self):
        self._lock = threading.Lock()
        self._is_scanning: bool = False
        self._cancel_requested = threading.Event()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._background_thread: Optional[threading.Thread] = None
        self._stop_background = threading.Event()

        self.ultima_varredura: Optional[datetime] = None
        self.proxima_varredura: Optional[datetime] = None
        self.ultimo_status_execucao: str = "Aguardando primeira varredura"
        self.total_varreduras: int = 0
        self.em_execucao: bool = False

        # Callbacks para atualizar interfaces gráficas (Desktop/Web)
        self.listeners: List[Callable[[Dict[str, Any]], None]] = []

    def register_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Registra ouvinte para receber eventos de progresso e finalização."""
        if callback not in self.listeners:
            self.listeners.append(callback)

    def _notificar_listeners(self, evento: Dict[str, Any]) -> None:
        for listener in list(self.listeners):
            try:
                listener(evento)
            except Exception as exc:
                logger.error("Erro em listener de monitoramento: %s", exc)

    def iniciar_servico_fundo(self, intervalo_segundos: int | None = None) -> None:
        """Inicia thread contínua de monitoramento em segundo plano."""
        intervalo = intervalo_segundos or Config.DEFAULT_SCAN_INTERVAL
        if self._background_thread and self._background_thread.is_alive():
            logger.warning("Serviço de fundo já em execução.")
            return

        self._stop_background.clear()

        def _loop():
            logger.info("Iniciando loop de monitoramento de fundo (intervalo: %ss).", intervalo)
            # Executa a primeira varredura após inicialização rápida (2s)
            time.sleep(2)
            while not self._stop_background.is_set():
                try:
                    self.executar_varredura()
                except Exception as exc:
                    logger.error("Exceção não tratada no loop de monitoramento: %s", exc)

                self.proxima_varredura = datetime.utcnow() + timedelta(seconds=intervalo)
                # Dormir em fatias pequenas para responder rápido a stop
                for _ in range(intervalo * 2):
                    if self._stop_background.is_set():
                        break
                    time.sleep(0.5)

        self._background_thread = threading.Thread(target=_loop, name="HaocMonitorWorker", daemon=True)
        self._background_thread.start()

    def parar_servico_fundo(self) -> None:
        """Sinaliza parada segura do serviço de fundo."""
        self._stop_background.set()
        self.cancelar_varredura()
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=3)
        logger.info("Serviço de monitoramento de fundo finalizado.")

    def cancelar_varredura(self) -> None:
        """Solicita cancelamento imediato da varredura em andamento."""
        if self._is_scanning:
            logger.info("Cancelamento seguro de varredura solicitado.")
            self._cancel_requested.set()

    def executar_varredura(self) -> Dict[str, Any]:
        """
        Executa uma varredura completa de todos os ramais ativos em paralelo.
        Garante que apenas uma varredura rode por vez.
        """
        if not self._lock.acquire(blocking=False):
            logger.warning("Tentativa de iniciar varredura bloqueada: outra varredura já está em execução.")
            return {"status": "ocupado", "mensagem": "Varredura já em andamento."}

        self._is_scanning = True
        self.em_execucao = True
        self._cancel_requested.clear()
        inicio_geral = datetime.utcnow()
        self.ultimo_status_execucao = "Em execução"

        self._notificar_listeners({"tipo": "VARREDURA_INICIADA", "inicio": inicio_geral.isoformat()})

        try:
            # 1. Carregar ramais ativos do banco
            with db.session_scope() as session:
                ramais = session.query(Ramal).filter(Ramal.ativo == True).all()
                ramais_dados = [
                    {
                        "id": r.id,
                        "ip": r.ip,
                        "status_anterior": r.status_atual,
                        "descricao": r.descricao,
                        "bloco": r.bloco,
                        "criticidade": r.criticidade,
                        "ultimo_visto_offline": r.ultimo_visto_offline,
                    }
                    for r in ramais
                ]

            total = len(ramais_dados)
            processados = 0
            online_count = 0
            offline_count = 0

            # 2. Execução paralela com pool de threads
            max_workers = min(Config.MAX_CONCURRENT_THREADS, max(5, total))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                self._executor = executor
                future_to_ramal = {
                    executor.submit(self._verificar_ramal_individual, r_data): r_data
                    for r_data in ramais_dados
                }

                for future in as_completed(future_to_ramal):
                    if self._cancel_requested.is_set():
                        logger.warning("Varredura cancelada pelo operador durante o processamento.")
                        self.ultimo_status_execucao = "Cancelada pelo usuário"
                        break

                    try:
                        resultado = future.result()
                        processados += 1
                        if resultado["status"] == StatusRamal.ONLINE.value:
                            online_count += 1
                        elif resultado["status"] == StatusRamal.OFFLINE.value:
                            offline_count += 1

                        self._notificar_listeners({
                            "tipo": "PROGRESSO",
                            "processados": processados,
                            "total": total,
                            "resultado_individual": resultado,
                        })
                    except Exception as exc:
                        logger.error("Erro ao obter resultado de ramal: %s", exc)

            fim_geral = datetime.utcnow()
            self.ultima_varredura = fim_geral
            self.total_varreduras += 1
            if not self._cancel_requested.is_set():
                self.ultimo_status_execucao = f"Concluída com sucesso ({processados}/{total})"

            sumario = {
                "status": "concluido",
                "total": total,
                "processados": processados,
                "online": online_count,
                "offline": offline_count,
                "inicio": inicio_geral.isoformat(),
                "fim": fim_geral.isoformat(),
                "duracao_segundos": round((fim_geral - inicio_geral).total_seconds(), 2),
            }

            self._notificar_listeners({"tipo": "VARREDURA_CONCLUIDA", "sumario": sumario})
            return sumario

        except Exception as exc:
            logger.critical("Falha grave durante execução da varredura: %s", exc)
            self.ultimo_status_execucao = f"Falha: {str(exc)}"
            return {"status": "erro", "mensagem": str(exc)}

        finally:
            self._is_scanning = False
            self.em_execucao = False
            self._executor = None
            self._lock.release()

    def _verificar_ramal_individual(self, r_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa o ping individual, gerencia a transição de estado e persiste incidentes.
        Cada verificação usa sua própria sessão isolada com tratamento de exceção.
        """
        ramal_id = r_data["id"]
        ip = r_data["ip"]
        status_anterior = r_data["status_anterior"]
        agora = datetime.utcnow()

        # 1. Checagem de IP
        if not ip:
            novo_status = StatusRamal.OFFLINE.value
            latencia = None
            erro = "Ramal sem endereço IP cadastrado"
        elif not validar_ipv4(ip):
            novo_status = StatusRamal.OFFLINE.value
            latencia = None
            erro = f"Endereço IP inválido ({ip})"
        else:
            sucesso, lat, err_msg = executar_ping(
                ip,
                timeout_seconds=Config.DEFAULT_PING_TIMEOUT,
                retries=Config.DEFAULT_PING_RETRIES,
            )
            if sucesso:
                novo_status = StatusRamal.ONLINE.value
                latencia = lat
                erro = None
            else:
                novo_status = StatusRamal.OFFLINE.value
                latencia = None
                erro = err_msg or "Indisponibilidade de rede"

        # 2. Persistência de estado e incidentes no SQLite
        try:
            with db.session_scope() as session:
                ramal = session.query(Ramal).filter(Ramal.id == ramal_id).first()
                if not ramal:
                    return {"ramal_id": ramal_id, "status": novo_status}

                # Registrar histórico em monitoramentos
                monit = Monitoramento(
                    ramal_id=ramal.id,
                    status=novo_status,
                    latencia=latencia,
                    verificado_em=agora,
                    erro=erro,
                )
                session.add(monit)

                # Máquina de estados para incidentes
                incidente_aberto_id = None
                if status_anterior != StatusRamal.OFFLINE.value and novo_status == StatusRamal.OFFLINE.value:
                    # TRANSIÇÃO: Ramal caiu (abrir novo incidente)
                    ramal.ultimo_visto_offline = agora
                    incidente = Incidente(
                        ramal_id=ramal.id,
                        iniciado_em=agora,
                        ip_monitorado=ramal.ip,
                        mac_cisco=ramal.mac_cisco,
                        bloco=ramal.bloco,
                        status_anterior=status_anterior,
                        novo_status=novo_status,
                        causa=erro or "Indisponibilidade de rede",
                    )
                    session.add(incidente)
                    session.flush()
                    incidente_aberto_id = incidente.id
                    logger.warning("Incidente aberto [#%s] para ramal %s", incidente.id, ramal.descricao)

                elif status_anterior == StatusRamal.OFFLINE.value and novo_status == StatusRamal.ONLINE.value:
                    # TRANSIÇÃO: Ramal recuperou (fechar incidente aberto)
                    incidente = session.query(Incidente).filter(
                        Incidente.ramal_id == ramal.id,
                        Incidente.encerrado_em == None,
                    ).order_by(Incidente.iniciado_em.desc()).first()

                    duracao_sec = 0
                    if incidente:
                        duracao_sec = int((agora - incidente.iniciado_em).total_seconds())
                        incidente.encerrado_em = agora
                        incidente.duracao = duracao_sec
                        incidente.latencia_final = latencia
                        incidente.novo_status = StatusRamal.ONLINE.value
                        logger.info("Incidente fechado [#%s] para ramal %s. Duração: %ss", incidente.id, ramal.descricao, duracao_sec)

                    ramal.ultimo_visto_online = agora
                    # Dispara notificação de restabelecimento se tiver demorado mais que o threshold
                    if duracao_sec >= Config.ALERT_MIN_OFFLINE_SECONDS:
                        alert_mgr.notificar_recuperacao(ramal.id, incidente.id if incidente else 0, duracao_sec)

                elif novo_status == StatusRamal.OFFLINE.value:
                    # Permanece offline: checar se deve disparar alerta de tempo prolongado
                    if ramal.ultimo_visto_offline:
                        off_sec = int((agora - ramal.ultimo_visto_offline).total_seconds())
                        inc = session.query(Incidente).filter(
                            Incidente.ramal_id == ramal.id,
                            Incidente.encerrado_em == None,
                        ).first()
                        if inc:
                            alert_mgr.notificar_queda(ramal.id, inc.id, off_sec)

                # Atualizar campos operacionais do ramal
                ramal.status_atual = novo_status
                ramal.ultima_verificacao = agora
                ramal.ultima_latencia = latencia
                ramal.ultimo_erro = erro
                if novo_status == StatusRamal.ONLINE.value:
                    ramal.ultimo_visto_online = agora

        except Exception as exc:
            logger.error("Erro ao persistir verificação do ramal %s: %s", ramal_id, exc)

        return {
            "ramal_id": ramal_id,
            "ip": ip,
            "status": novo_status,
            "latencia": latencia,
            "erro": erro,
            "verificado_em": agora.isoformat(),
        }

    def calcular_estatisticas(self) -> Dict[str, Any]:
        """Calcula métricas agregadas executivas para o dashboard."""
        with db.session_scope() as session:
            ramais = session.query(Ramal).filter(Ramal.ativo == True).all()
            total = len(ramais)
            online = sum(1 for r in ramais if r.status_atual == StatusRamal.ONLINE.value)
            offline = sum(1 for r in ramais if r.status_atual == StatusRamal.OFFLINE.value)
            inativos = session.query(Ramal).filter(Ramal.ativo == False).count()
            sem_ip = sum(1 for r in ramais if not r.ip or not r.ip.strip())

            latencias = [r.ultima_latencia for r in ramais if r.status_atual == StatusRamal.ONLINE.value and r.ultima_latencia]
            latencia_media = round(sum(latencias) / len(latencias), 1) if latencias else 0.0

            disponibilidade = round((online / total * 100), 1) if total > 0 else 100.0

            # Estatísticas por bloco
            blocos_map: Dict[str, Dict[str, Any]] = {}
            for r in ramais:
                b = r.bloco or "Geral"
                if b not in blocos_map:
                    blocos_map[b] = {"nome": b, "total": 0, "online": 0, "offline": 0, "latencias": []}
                blocos_map[b]["total"] += 1
                if r.status_atual == StatusRamal.ONLINE.value:
                    blocos_map[b]["online"] += 1
                    if r.ultima_latencia:
                        blocos_map[b]["latencias"].append(r.ultima_latencia)
                elif r.status_atual == StatusRamal.OFFLINE.value:
                    blocos_map[b]["offline"] += 1

            blocos_lista = []
            for b_nome, b_dados in blocos_map.items():
                b_tot = b_dados["total"]
                b_on = b_dados["online"]
                b_pct = round((b_on / b_tot * 100), 1) if b_tot > 0 else 0.0
                b_lat_media = round(sum(b_dados["latencias"]) / len(b_dados["latencias"]), 1) if b_dados["latencias"] else None
                blocos_lista.append({
                    "nome": b_nome,
                    "total": b_tot,
                    "online": b_on,
                    "offline": b_dados["offline"],
                    "disponibilidade": b_pct,
                    "latencia_media": b_lat_media,
                })

            # Ranking dos ramais com maior quantidade de quedas
            from sqlalchemy import func
            ranking_quedas = (
                session.query(
                    Ramal.id,
                    Ramal.descricao,
                    Ramal.bloco,
                    Ramal.ip,
                    func.count(Incidente.id).label("total_quedas"),
                    func.coalesce(func.sum(Incidente.duracao), 0).label("tempo_total_offline"),
                )
                .join(Incidente, Incidente.ramal_id == Ramal.id)
                .group_by(Ramal.id)
                .order_by(func.count(Incidente.id).desc())
                .limit(5)
                .all()
            )

            ranking = [
                {
                    "ramal_id": rq[0],
                    "descricao": rq[1],
                    "bloco": rq[2],
                    "ip": rq[3],
                    "quedas": rq[4],
                    "tempo_offline_formatado": Ramal._format_duration(rq[5]),
                }
                for rq in ranking_quedas
            ]

        return {
            "total_cadastrados": total,
            "online": online,
            "offline": offline,
            "inativos": inativos,
            "sem_ip": sem_ip,
            "percentual_disponibilidade": disponibilidade,
            "latencia_media": latencia_media,
            "ultima_varredura": self.ultima_varredura.strftime("%H:%M:%S - %d/%m/%Y") if self.ultima_varredura else "Nenhuma",
            "proxima_varredura": self.proxima_varredura.strftime("%H:%M:%S") if self.proxima_varredura else "Em breve",
            "status_monitoramento": self.ultimo_status_execucao,
            "em_execucao": self.em_execucao,
            "blocos": blocos_lista,
            "ranking_quedas": ranking,
        }


# Instância global do motor de monitoramento
monitor_engine = MonitorEngine()
