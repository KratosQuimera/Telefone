"""
Testes do Motor de Monitoramento, Transição de Status e SLA.
Utiliza mocks para comandos de ping sem dependência de rede externa.
"""
from datetime import datetime, timedelta
from haoc_voip.core.monitor import MonitorEngine, monitor_engine
from haoc_voip.core.models import Ramal, Incidente, StatusRamal
from haoc_voip.core.database import db
import haoc_voip.core.monitor as monitor_module


def test_monitor_state_transition_and_incident(monkeypatch):
    """Testa transição ONLINE -> OFFLINE -> ONLINE com geração e encerramento de incidente."""
    engine = MonitorEngine()

    # Inserir um ramal específico para o teste
    with db.session_scope() as session:
        ramal = Ramal(
            descricao="8888 - Teste Monitor",
            bloco="BLOCO TESTE",
            ip="192.168.88.88",
            mac_cisco="00:1B:54:88:88:88",
            status_atual=StatusRamal.ONLINE.value,
            ativo=True,
        )
        session.add(ramal)
        session.flush()
        ramal_id = ramal.id

    # 1. Simular falha de ping (ramal offline)
    monkeypatch.setattr(monitor_module, "executar_ping", lambda ip, timeout_seconds, retries: (False, None, "Host unreachable"))

    # Executar varredura
    resumo = engine.executar_varredura()
    assert resumo["offline"] >= 1

    with db.session_scope() as session:
        r = session.query(Ramal).filter(Ramal.id == ramal_id).first()
        assert r.status_atual == StatusRamal.OFFLINE.value
        assert r.ultimo_visto_offline is not None

        # Deve haver um incidente aberto
        inc = session.query(Incidente).filter(Incidente.ramal_id == ramal_id, Incidente.encerrado_em == None).first()
        assert inc is not None
        assert inc.novo_status == StatusRamal.OFFLINE.value

    # 2. Simular retorno da conexão (ping com sucesso)
    monkeypatch.setattr(monitor_module, "executar_ping", lambda ip, timeout_seconds, retries: (True, 4.5, None))

    # Executar nova varredura
    resumo2 = engine.executar_varredura()
    assert resumo2["online"] >= 1

    with db.session_scope() as session:
        r = session.query(Ramal).filter(Ramal.id == ramal_id).first()
        assert r.status_atual == StatusRamal.ONLINE.value
        assert r.ultima_latencia == 4.5

        # O incidente anterior deve ter sido encerrado
        inc_encerrado = session.query(Incidente).filter(Incidente.ramal_id == ramal_id, Incidente.encerrado_em != None).first()
        assert inc_encerrado is not None
        assert inc_encerrado.duracao is not None


def test_sla_calculation():
    """Testa o cálculo da taxa de disponibilidade operacional."""
    engine = MonitorEngine()
    stats = engine.calcular_estatisticas()

    assert "total_cadastrados" in stats
    assert "online" in stats
    assert "offline" in stats
    assert "percentual_disponibilidade" in stats
    assert 0.0 <= stats["percentual_disponibilidade"] <= 100.0
