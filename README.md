# HAOC VoIP Monitor Enterprise

Sistema Integrado de Monitoramento, Diagnóstico e Gestão de Ramais VoIP Cisco para o Hospital Augusto de Oliveira Camargo (HAOC).

---

## 1. Visão Geral

O **HAOC VoIP Monitor Enterprise** foi desenvolvido especificamente para atender à criticidade operacional do ambiente hospitalar da Tecnologia da Informação do HAOC. O sistema permite que analistas de suporte e infraestrutura monitorem em tempo real a disponibilidade de ramais telefônicos Cisco (séries 7800, 8800 e legados), identifiquem falhas antes do impacto em áreas assistenciais (UTIs, Centro Cirúrgico, Pronto Socorro), acompanhem o histórico completo de incidentes e sincronizem a base com arquivos legados em JSON com segurança transacional e trilha de auditoria.

### Principais Diferenciais
* **Dualidade de Interfaces**: 
  * **Dashboard Web (Flask)**: Acesso via navegador para monitoramento centralizado, visualização executiva de SLA, relatórios, métricas por bloco e gestão de usuários.
  * **Aplicação Desktop (PyQt6)**: Interface nativa Windows 10/11 rica em recursos para analistas de suporte, com visualização em cartões estilizados, atalhos de teclado, pesquisa dinâmica instantânea e varreduras manuais/automáticas.
* **Motor Assíncrono Concorrente**: Execução paralela com `ThreadPoolExecutor`, ping adaptativo para Windows e Linux, timeouts estritos e sem travamento de interface gráfica.
* **Integridade Hospitalar (SQLite com WAL)**: Uso do SQLite configurado com `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON` e `busy_timeout=10000` para permitir concorrência total entre leitura no web/desktop e gravação no motor de monitoramento.
* **Sincronização Segura de JSON com Diff Visual**: Importador do formato legado JSON que compara a base cadastrada com o arquivo, exibindo novos ramais, alterações de IP/MAC e ramais removidos, com backup prévio automático antes de qualquer modificação.
* **Controle de Acesso Baseado em Papéis (RBAC)**: Perfis de Administrador, Analista e Visualizador com senhas protegidas via PBKDF2-SHA256, proteção contra força bruta e log detalhado de auditoria de cada ação.

---

## 2. Estrutura do Projeto

```
haoc_voip/
├── config.py                 # Configurações centralizadas e variáveis de ambiente
├── core/                     # Núcleo da lógica de negócio e persistência
│   ├── models.py             # Modelos relacionais SQLAlchemy (Ramais, Incidentes, etc.)
│   ├── database.py           # Conexão thread-safe SQLite e engine WAL
│   ├── auth.py               # PBKDF2 hashing, lockout e controle de sessões
│   ├── monitor.py            # Motor de varredura concorrente, ping e cálculo de SLA
│   ├── importer.py           # Motor de diffing e importação/exportação JSON legado
│   └── backup.py             # Gestor de snapshots atômicos e retenção
├── desktop/                  # Interface Desktop PyQt6 (Windows/Linux)
│   ├── styles.py             # Folhas de estilo corporativas hospitalares (QSS)
│   ├── signals.py            # Sinais Qt para thread-safety
│   ├── login_dialog.py       # Modal de autenticação
│   ├── ramal_dialog.py       # Modal de criação e edição com validações
│   ├── incidentes_dialog.py  # Consulta e anotação de histórico de indisponibilidade
│   ├── import_dialog.py      # Assistente de diff visual e importação seletiva
│   └── main_window.py        # Janela principal com grid de cartões e filtros
├── web/                      # Servidor Web Flask (Jinja2 + CSS Corporativo)
│   ├── app.py                # Fábrica da aplicação Flask e rotas centrais
│   ├── routes/               # Blueprints (auth, ramais, incidentes, relatorios, etc.)
│   ├── static/               # Folha de estilo corporativa e assets
│   └── templates/            # Templates Jinja2 responsivos e acessíveis
data/                         # Diretório de persistência SQLite e backups
tests/                        # Suíte de testes automatizados com pytest
init_db.py                    # Script de inicialização e carga de dados demo
web_main.py                   # Ponto de entrada do servidor web Flask
desktop_main.py               # Ponto de entrada da aplicação desktop PyQt6
server.ts                     # Gateway de integração e proxy do ambiente
```

---

## 3. Requisitos e Instalação

### Pré-requisitos
* Python 3.10 ou superior (testado em 3.11/3.12).
* No Windows 10/11: PowerShell ou Prompt de Comando.
* Dependências listadas em `requirements.txt`.

### Instalação das Dependências

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Windows:
.\venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

# Instalar pacotes obrigatórios
pip install -r requirements.txt
```

---

## 4. Inicialização do Banco de Dados

Para criar as tabelas SQLite e semear as credenciais de teste e ramais hospitalares demonstrativos:

```bash
python init_db.py
```

### Credenciais Padrão Criadas:
| Login | Senha Inicial | Perfil | Permissões |
|---|---|---|---|
| `Wagner` | `SenhaTel@Haoc` | Administrador Master | Acesso total irrestrito, gestão master, usuários, backups, configs |
| `admin` | `Admin@HAOC2026` | Administrador | Acesso total, gerenciamento de usuários, backups, configs |
| `analista` | `Analista@HAOC2026` | Analista | Monitoramento, cadastro/edição de ramais, importação, incidentes |
| `visualizador`| `Visu@HAOC2026` | Visualização | Apenas consulta de status, dashboard e relatórios |

---

## 5. Como Executar as Aplicações

### 5.1 Dashboard Web (Flask)
Para iniciar o dashboard web diretamente via Python:
```bash
python web_main.py
```
O servidor estará disponível no navegador no endereço:
`http://localhost:5050` (ou na porta 3000 pelo gateway integrado).

### 5.2 Aplicação Desktop (PyQt6 no Windows 10/11)
Para iniciar a aplicação gráfica desktop em modo script:
```bash
python desktop_main.py
```
1. Informe suas credenciais no diálogo de login.
2. Navegue pelos blocos e ramais no grid de cartões.
3. Utilize os botões **Verificar Todos Agora**, **Novo Ramal**, **Importar JSON** e **Incidentes**.

### 5.3 Como Gerar o Executável Windows (.exe)
Para distribuir a aplicação como um executável nativo Windows sem necessidade do usuário ter Python instalado:

* **Opção 1 (Automático via Windows Batch - 1 Clique)**:
  Dê um duplo clique no arquivo `build_windows.bat`. Ele verificará o Python, instalará o PyInstaller e gerará o arquivo `dist\HAOC_VoIP_Monitor.exe`.

* **Opção 2 (Via Linha de Comando / PowerShell)**:
  ```bash
  python build_exe.py
  ```
  Ou diretamente com a especificação PyInstaller:
  ```bash
  pyinstaller --clean haoc_voip_desktop.spec
  ```

O executável final independente estará pronto na pasta `dist/HAOC_VoIP_Monitor.exe`.

---

## 6. Funcionalidades Principais

### Motor de Monitoramento e SLA
* **Verificação Concorrente**: Realiza testes de ping em lotes paralelos configuráveis (padrão de 25 threads).
* **Cálculo Automático de SLA**: Calcula a taxa percentual de disponibilidade da infraestrutura de telefonia por bloco e global.
* **Ciclo de Vida de Incidentes**: Ao detectar que um ramal ficou offline, abre imediatamente um incidente registrando data, hora, IP e causa. Quando o ramal retorna ao status ONLINE, encerra o incidente gravando a duração exata da indisponibilidade em segundos.

### Assistente de Importação com Comparação Visual (Diff)
* Suporte total ao formato legado JSON:
```json
{
  "BLOCO A": [
    {
      "Descrição": "1001 - Recepção Central",
      "I.P": "192.168.10.15",
      "I.P Cisco": "00:1B:54:12:34:56",
      "Modelo": "Cisco CP-7821"
    }
  ]
}
```
* **Detecção Inteligente**: Identifica ramais novos, alterações parciais (ex: mudança apenas de IP ou modelo) e itens que foram retirados do arquivo.
* **Segurança Absoluta**: Realiza backup atômico do banco de dados antes de aplicar qualquer alteração.

---

## 7. Execução dos Testes Automatizados

O sistema conta com suíte completa de testes unitários e de integração utilizando `pytest`, cobrindo validações de rede com mocks, cálculo de SLA, regras de autenticação, transições de estado e operações de backup.

Para rodar todos os testes:
```bash
pytest -v
```

---

## 8. Segurança e Conformidade
* **Armazenamento de Senhas**: Utiliza derivação com sal criptográfico aleatório (PBKDF2-HMAC-SHA256 com 100.000 iterações).
* **Mitigação de Ataques**: Bloqueio temporário automático da conta após 5 tentativas incorretas consecutivas.
* **Auditoria de Operações**: Todas as ações administrativas e modificações de ramais geram registros imutáveis na tabela `auditoria`, contendo usuário, IP de origem, timestamp e detalhes da alteração.
