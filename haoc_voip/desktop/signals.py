"""
Sinais Qt (PyQt6) para Comunicação Assíncrona Segura entre Threads e Interface.
Evita travamento da interface gráfica durante varreduras paralelas e testes de ping.
"""
from PyQt6.QtCore import QObject, pyqtSignal


class WorkerSignals(QObject):
    """Sinais emitidos por tarefas em segundo plano para atualização de interface."""
    # Sinais de Varredura Completa
    scan_started = pyqtSignal()
    scan_progress = pyqtSignal(int, int, str)  # concluidos, total, mensagem
    scan_finished = pyqtSignal(dict)           # resumo_estatisticas
    scan_canceled = pyqtSignal()

    # Sinal de Ping Individual
    ping_result = pyqtSignal(int, bool, float, str)  # ramal_id, sucesso, latencia, erro

    # Sinal de Atualização Geral do Banco de Dados
    data_reloaded = pyqtSignal()

    # Sinal de Alerta Crítico
    alert_triggered = pyqtSignal(str, str)  # titulo, mensagem


signals = WorkerSignals()
