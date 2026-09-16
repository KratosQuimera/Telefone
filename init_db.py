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
                ("BLOCO A - INTERNAÇÃO", "#0284c7"),
                ("BLOCO B - DIAGNÓSTICO", "#0d9488"),
                ("PRONTO SOCORRO", "#dc2626"),
                ("UTI GERAL", "#b91c1c"),
                ("CENTRO CIRÚRGICO", "#7c3aed"),
                ("AMBULATÓRIO", "#ca8a04"),
                ("FARMÁCIA CENTRAL", "#16a34a"),
            ]
            for b_nome, cor in blocos_info:
                if not session.query(Bloco).filter(Bloco.nome == b_nome).first():
                    session.add(Bloco(nome=b_nome, cor=cor, ativo=True))

            setores_info = [
                "Recepção Central",
                "Triagem e Classificação",
                "Posto de Enfermagem 1",
                "Posto de Enfermagem 2",
                "Sala de Emergência Vermelha",
                "Box UTI Leito 01 a 10",
                "Expedição Farmácia",
                "Supervisão TI e Infra",
            ]
            for s_nome in setores_info:
                if not session.query(Setor).filter(Setor.nome == s_nome).first():
                    session.add(Setor(nome=s_nome, ativo=True))

            session.flush()

            # 5. Ramais VoIP Cisco demonstrativos
            ramais_exemplo = [
                # Bloco A
                ("Cisco CP-7821", "00:1B:54:A1:10:01", "1001 - Recepção Principal A", "127.0.0.1", "BLOCO A - INTERNAÇÃO", "Recepção Central", "Térreo - Hall de Entrada", "ALTA"),
                ("Cisco CP-8841", "00:1B:54:A1:10:02", "1002 - Posto de Enfermagem 2º Andar", "127.0.0.1", "BLOCO A - INTERNAÇÃO", "Posto de Enfermagem 1", "2º Andar - Ala Norte", "CRITICA"),
                ("Cisco CP-3905", "00:1B:54:A1:10:03", "1003 - Quarto Isolamento 204", "192.168.10.15", "BLOCO A - INTERNAÇÃO", "Posto de Enfermagem 1", "2º Andar - Quarto 204", "NORMAL"),
                
                # Pronto Socorro (Crítico)
                ("Cisco CP-8845", "00:1B:54:B2:20:01", "2001 - Triagem e Acolhimento PS", "127.0.0.1", "PRONTO SOCORRO", "Triagem e Classificação", "Portão PS 24h", "CRITICA"),
                ("Cisco CP-8861", "00:1B:54:B2:20:02", "2002 - Sala Vermelha Emergência", "127.0.0.1", "PRONTO SOCORRO", "Sala de Emergência Vermelha", "Sala 01 - Ressuscitação", "CRITICA"),
                ("Cisco CP-7821", "00:1B:54:B2:20:03", "2003 - Guichê Atendimento PS", "192.168.20.22", "PRONTO SOCORRO", "Recepção Central", "Balcão Atendimento", "ALTA"),

                # UTI Geral (Crítico)
                ("Cisco CP-8841", "00:1B:54:C3:30:01", "3001 - Posto Central UTI Geral", "127.0.0.1", "UTI GERAL", "Box UTI Leito 01 a 10", "3º Andar UTI", "CRITICA"),
                ("Cisco CP-7821", "00:1B:54:C3:30:02", "3002 - Prescrição Médica UTI", "192.168.30.12", "UTI GERAL", "Box UTI Leito 01 a 10", "Ilha Médica 02", "CRITICA"),

                # Centro Cirúrgico
                ("Cisco CP-8845", "00:1B:54:D4:40:01", "4001 - Recepção Centro Cirúrgico", "127.0.0.1", "CENTRO CIRÚRGICO", "Recepção Central", "4º Andar Bloco Cirúrgico", "CRITICA"),
                ("Cisco CP-7821", "00:1B:54:D4:40:02", "4002 - Sala de Recuperação Anestésica", "192.168.40.18", "CENTRO CIRÚRGICO", "Posto de Enfermagem 2", "RPA Sala 3", "ALTA"),

                # Farmácia e Infra
                ("Cisco CP-7821", "00:1B:54:E5:50:01", "5001 - Balcão Farmácia Central", "127.0.0.1", "FARMÁCIA CENTRAL", "Expedição Farmácia", "Subsolo Farmácia", "ALTA"),
                ("Cisco CP-8861", "00:1B:54:F6:60:01", "6001 - NOC / Suporte Infra TI", "127.0.0.1", "BLOCO B - DIAGNÓSTICO", "Supervisão TI e Infra", "1º Andar Datacenter", "CRITICA"),
                ("Cisco CP-3905", "", "6002 - Sala Técnica Sem IP", "", "BLOCO B - DIAGNÓSTICO", "Supervisão TI e Infra", "Rack 03", "NORMAL"),
            ]

            for mod, mac, desc, ip, blk, setr, loc, crit in ramais_exemplo:
                if not session.query(Ramal).filter(Ramal.descricao == desc).first():
                    r = Ramal(
                        modelo=mod,
                        mac_cisco=mac or None,
                        descricao=desc,
                        ip=ip or None,
                        bloco=blk,
                        setor=setr,
                        localizacao=loc,
                        criticidade=crit,
                        ativo=True,
                    )
                    session.add(r)
            print(f"[+] {len(ramais_exemplo)} ramais VoIP demonstrativos cadastrados.")

    print("=" * 65)
    print("Banco de dados configurado com sucesso!")
    print("Credenciais de acesso padrão:")
    print("  - Administrador : admin / Admin@HAOC2026")
    print("  - Analista      : analista / Analista@HAOC2026")
    print("  - Visualizador  : visualizador / Visu@HAOC2026")
    print("=" * 65)


if __name__ == "__main__":
    seed_database()
