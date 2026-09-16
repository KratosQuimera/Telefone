"""
Script de Inicialização do Banco de Dados SQLite e Criação do Administrador Inicial.
Executável via linha de comando: python init_db.py
"""
import sys
from datetime import datetime

from haoc_voip.config import Config
from haoc_voip.core.models import Base, Usuario, Bloco, Setor, Ramal, Configuracao, PerfilUsuario
from haoc_voip.core.database import db
from haoc_voip.core.auth import hash_senha
from haoc_voip.core.audit import registrar_auditoria


def seed_database(criar_dados_demo: bool = True):
    """Inicializa tabelas, configurações padrão, usuários e ramais demonstrativos."""
    print("=" * 65)
    print("HAOC VoIP Monitor Enterprise - Inicializador de Banco de Dados")
    print("=" * 65)

    # 1. Criação das tabelas
    db.init_db()
    print("[+] Tabelas criadas com sucesso no SQLite (WAL mode ativado).")

    with db.session_scope() as session:
        # 2. Configurações padrão
        configs_padrao = [
            ("ping_timeout", str(Config.DEFAULT_PING_TIMEOUT), "Timeout do ping em segundos", "float"),
            ("ping_retries", str(Config.DEFAULT_PING_RETRIES), "Tentativas antes de considerar falha", "int"),
            ("scan_interval", str(Config.DEFAULT_SCAN_INTERVAL), "Intervalo periódico entre varreduras (s)", "int"),
            ("max_threads", str(Config.MAX_CONCURRENT_THREADS), "Limite de concorrência paralela", "int"),
            ("alert_min_offline", str(Config.ALERT_MIN_OFFLINE_SECONDS), "Tempo mínimo offline para alerta (s)", "int"),
            ("hospital_name", "Hospital das Clínicas - HAOC", "Nome da instituição hospitalar", "string"),
        ]
        for chave, val, desc, tipo in configs_padrao:
            if not session.query(Configuracao).filter(Configuracao.chave == chave).first():
                session.add(Configuracao(chave=chave, valor=val, descricao=desc, tipo=tipo))
        print("[+] Configurações operacionais registradas.")

        # 3. Usuários essenciais
        usuarios_padrao = [
            ("Wagner - Administrador Master", "Wagner", "SenhaTel@Haoc", PerfilUsuario.ADMINISTRADOR.value),
            ("Administrador do Sistema", "admin", "Admin@HAOC2026", PerfilUsuario.ADMINISTRADOR.value),
            ("Analista de Suporte TI", "analista", "Analista@HAOC2026", PerfilUsuario.ANALISTA.value),
            ("Painel de Visualização (NOC)", "visualizador", "Visu@HAOC2026", PerfilUsuario.VISUALIZACAO.value),
        ]
        for nome, login, senha, perfil in usuarios_padrao:
            existente = session.query(Usuario).filter(
                (Usuario.login == login) | (Usuario.login == login.lower())
            ).first()
            if not existente:
                novo_u = Usuario(
                    nome=nome,
                    login=login,
                    senha_hash=hash_senha(senha),
                    perfil=perfil,
                    ativo=True,
                )
                session.add(novo_u)
                print(f"[+] Usuário criado: {login} (Perfil: {perfil})")
            else:
                existente.senha_hash = hash_senha(senha)
                existente.perfil = perfil
                existente.ativo = True
                print(f"[+] Usuário atualizado/validado: {login} (Perfil: {perfil})")

        # 4. Blocos e Setores hospitalares
        if criar_dados_demo:
            blocos_info = [
                ("Bloco Central", "#0284c7"),
                ("Pronto Socorro", "#dc2626"),
                ("UTI Geral", "#b91c1c"),
                ("Centro Cirúrgico", "#7c3aed"),
                ("Maternidade", "#ec4899"),
                ("Ambulatório", "#ca8a04"),
                ("Administrativo", "#0d9488"),
            ]
            for b_nome, cor in blocos_info:
                if not session.query(Bloco).filter(Bloco.nome == b_nome).first():
                    session.add(Bloco(nome=b_nome, cor=cor, ativo=True))

            setores_info = [
                "Recepção",
                "Triagem",
                "Consultórios",
                "Enfermagem",
                "Coordenação",
                "Salas Cirúrgicas",
                "RPA",
                "Internação",
                "Atendimento",
                "Tecnologia da Informação",
                "Diretoria",
                "Farmácia",
                "CDI",
            ]
            for s_nome in setores_info:
                if not session.query(Setor).filter(Setor.nome == s_nome).first():
                    session.add(Setor(nome=s_nome, ativo=True))

            session.flush()

            # 5. Ramais VoIP Cisco demonstrativos sincronizados com store.json (13 ramais)
            ramais_exemplo = [
                ("Cisco CP-7841", "00:27:0D:A1:B2:C1", "Ramal 2001 - Recepção Central - Atendimento Geral", "192.168.10.11", "Bloco Central", "Recepção", "Térreo Hall Central", "NORMAL", "ONLINE", 10.0),
                ("Cisco CP-8841", "00:27:0D:A1:B2:C2", "Ramal 2002 - Triagem Adulto - Emergência", "192.168.10.12", "Pronto Socorro", "Triagem", "Portão PS 24h", "CRITICA", "ONLINE", 15.0),
                ("Cisco CP-3905", "00:27:0D:A1:B2:C3", "Ramal 2003 - Consultório 01 - Emergência Clínica", "192.168.10.13", "Pronto Socorro", "Consultórios", "Consultório 01", "ALTA", "ONLINE", 5.0),
                ("Cisco CP-8845", "00:27:0D:A1:B2:C4", "Ramal 2010 - Posto de Enfermagem UTI Geral", "192.168.10.20", "UTI Geral", "Enfermagem", "3º Andar UTI", "CRITICA", "ONLINE", 23.0),
                ("Cisco CP-7841", "00:27:0D:A1:B2:C5", "Ramal 2011 - Coordenação Médica UTI", "192.168.10.21", "UTI Geral", "Coordenação", "Ilha Médica 02", "CRITICA", "ONLINE", 10.0),
                ("Cisco CP-7821", "00:27:0D:A1:B2:C6", "Ramal 2020 - Sala de Cirurgia 01 - Interfone", "192.168.10.30", "Centro Cirúrgico", "Salas Cirúrgicas", "Sala Cirúrgica 01", "CRITICA", "ONLINE", 14.0),
                ("Cisco CP-7821", "00:27:0D:A1:B2:C7", "Ramal 2021 - Sala de Recuperação Anestésica (RPA)", "192.168.10.31", "Centro Cirúrgico", "RPA", "RPA Leito 03", "ALTA", "ONLINE", 11.0),
                ("Cisco CP-3905", "00:27:0D:A1:B2:C8", "Ramal 2030 - Posto Maternidade 2º Andar", "192.168.10.40", "Maternidade", "Internação", "2º Andar Ala Maternidade", "NORMAL", "ONLINE", 18.0),
                ("Cisco CP-7841", "00:27:0D:A1:B2:C9", "Ramal 2040 - Agendamento de Consultas - Ambulatório", "192.168.10.50", "Ambulatório", "Atendimento", "Balcão Agendamento", "NORMAL", "ONLINE", 22.0),
                ("Cisco CP-8861", "00:27:0D:A1:B2:CA", "Ramal 2050 - TI - Central de Serviços e Telefonia", "192.168.10.60", "Administrativo", "Tecnologia da Informação", "1º Andar Datacenter NOC", "CRITICA", "ONLINE", 4.0),
                ("Cisco CP-8845", "00:27:0D:A1:B2:CB", "Ramal 2051 - Diretoria Clínica HAOC", "192.168.10.61", "Administrativo", "Diretoria", "Gabinete Diretoria", "ALTA", "ONLINE", 8.0),
                ("Cisco CP-7841", "00:27:0D:B1:C2:E1", "Ramal 2060 - Farmácia Central - Balcão 1", "192.168.10.80", "Bloco Central", "Farmácia", "Balcão 1 Farmácia", "ALTA", "ONLINE", 12.0),
                ("Cisco CP-8845", "00:27:0D:B1:C2:E2", "Ramal 2061 - Centro de Diagnóstico por Imagem (CDI) - Tomografia", "192.168.10.81", "Bloco Central", "CDI", "Sala Tomografia", "ALTA", "ONLINE", 6.0),
            ]

            # Limpar e recarregar para garantir sincronia
            session.query(Ramal).delete()
            for mod, mac, desc, ip, blk, setr, loc, crit, st, lat in ramais_exemplo:
                r = Ramal(
                    modelo=mod,
                    mac_cisco=mac,
                    descricao=desc,
                    ip=ip,
                    bloco=blk,
                    setor=setr,
                    localizacao=loc,
                    criticidade=crit,
                    status_atual=st,
                    ultima_latencia=lat,
                    ativo=True,
                )
                session.add(r)
            print(f"[+] {len(ramais_exemplo)} ramais VoIP corporativos sincronizados.")

    print("=" * 65)
    print("Banco de dados configurado com sucesso!")
    print("Credenciais de acesso padrão:")
    print("  - Administrador : admin / Admin@HAOC2026")
    print("  - Analista      : analista / Analista@HAOC2026")
    print("  - Visualizador  : visualizador / Visu@HAOC2026")
    print("=" * 65)


if __name__ == "__main__":
    seed_database()
