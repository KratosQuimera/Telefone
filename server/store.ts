import fs from "fs";
import path from "path";
import crypto from "crypto";

export interface Ramal {
  id: number;
  numero: string;
  descricao: string;
  bloco: string;
  setor: string;
  ip: string;
  mac_cisco: string;
  modelo: string;
  status: "ONLINE" | "OFFLINE";
  latencia_ms: number | null;
  ultimo_ping: string | null;
  ativo: boolean;
  criado_em: string;
}

export interface Incidente {
  id: number;
  ramal_id: number;
  ramal_numero: string;
  ramal_descricao: string;
  bloco: string;
  setor: string;
  tipo: string;
  gravidade: "CRITICA" | "ALTA" | "MEDIA" | "BAIXA";
  status: "ABERTO" | "EM_ATENDIMENTO" | "RESOLVIDO";
  aberto_em: string;
  resolvido_em: string | null;
  duracao_minutos: number | null;
  observacoes: string;
}

export interface Usuario {
  id: number;
  nome: string;
  login: string;
  perfil: "ADMINISTRADOR" | "ANALISTA" | "VISUALIZACAO";
  ativo: boolean;
  ultimo_login: string | null;
}

export interface LogAuditoria {
  id: number;
  data_hora: string;
  usuario_nome: string;
  acao: string;
  detalhes: string;
}

export interface NetworkSyncConfig {
  caminho_rede: string;
  auto_sync: boolean;
  ultimo_sync: string | null;
  status: "OK" | "ERRO" | "NAO_CONFIGURADO";
  ultimo_erro: string | null;
  total_processados: number;
}

export interface DatabaseSchema {
  ramais: Ramal[];
  incidentes: Incidente[];
  usuarios: Usuario[];
  auditoria: LogAuditoria[];
}

const DATA_DIR = path.join(process.cwd(), "data");
const DB_PATH = path.join(DATA_DIR, "store.json");
const NETWORK_CONFIG_PATH = path.join(DATA_DIR, "network_config.json");

function hashPassword(pass: string): string {
  return crypto.createHash("sha256").update(pass + "HAOC_SALT_2026").digest("hex");
}

const SENHAS_MAP: Record<string, string> = {
  wagner: hashPassword("SenhaTel@Haoc"),
  admin: hashPassword("Admin@HAOC2026"),
  analista: hashPassword("Analista@HAOC2026"),
  visualizador: hashPassword("Visu@HAOC2026"),
};

function getInitialData(): DatabaseSchema {
  return {
    usuarios: [
      {
        id: 1,
        nome: "Wagner (Administrador Master)",
        login: "Wagner",
        perfil: "ADMINISTRADOR",
        ativo: true,
        ultimo_login: null,
      },
      {
        id: 2,
        nome: "Administrador do Sistema",
        login: "admin",
        perfil: "ADMINISTRADOR",
        ativo: true,
        ultimo_login: null,
      },
      {
        id: 3,
        nome: "Analista de Suporte TI",
        login: "analista",
        perfil: "ANALISTA",
        ativo: true,
        ultimo_login: null,
      },
      {
        id: 4,
        nome: "Painel de Visualização (NOC)",
        login: "visualizador",
        perfil: "VISUALIZACAO",
        ativo: true,
        ultimo_login: null,
      },
    ],
    ramais: [
      {
        id: 101,
        numero: "2001",
        descricao: "Recepção Central - Atendimento Geral",
        bloco: "Bloco Central",
        setor: "Recepção",
        ip: "192.168.10.11",
        mac_cisco: "00:27:0D:A1:B2:C1",
        modelo: "Cisco CP-7841",
        status: "ONLINE",
        latencia_ms: 12,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 102,
        numero: "2002",
        descricao: "Triagem Adulto - Emergência",
        bloco: "Pronto Socorro",
        setor: "Triagem",
        ip: "192.168.10.12",
        mac_cisco: "00:27:0D:A1:B2:C2",
        modelo: "Cisco CP-8841",
        status: "ONLINE",
        latencia_ms: 18,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 103,
        numero: "2003",
        descricao: "Consultório 01 - Emergência Clínica",
        bloco: "Pronto Socorro",
        setor: "Consultórios",
        ip: "192.168.10.13",
        mac_cisco: "00:27:0D:A1:B2:C3",
        modelo: "Cisco CP-3905",
        status: "ONLINE",
        latencia_ms: 15,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 104,
        numero: "2010",
        descricao: "Posto de Enfermagem UTI Geral",
        bloco: "UTI Geral",
        setor: "Enfermagem",
        ip: "192.168.10.20",
        mac_cisco: "00:27:0D:A1:B2:C4",
        modelo: "Cisco CP-8845",
        status: "ONLINE",
        latencia_ms: 9,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 105,
        numero: "2011",
        descricao: "Coordenação Médica UTI",
        bloco: "UTI Geral",
        setor: "Coordenação",
        ip: "192.168.10.21",
        mac_cisco: "00:27:0D:A1:B2:C5",
        modelo: "Cisco CP-7841",
        status: "OFFLINE",
        latencia_ms: null,
        ultimo_ping: new Date(Date.now() - 35 * 60000).toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 106,
        numero: "2020",
        descricao: "Sala de Cirurgia 01 - Interfone",
        bloco: "Centro Cirúrgico",
        setor: "Salas Cirúrgicas",
        ip: "192.168.10.30",
        mac_cisco: "00:27:0D:A1:B2:C6",
        modelo: "Cisco CP-7821",
        status: "ONLINE",
        latencia_ms: 14,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 107,
        numero: "2021",
        descricao: "Sala de Recuperação Anestésica (RPA)",
        bloco: "Centro Cirúrgico",
        setor: "RPA",
        ip: "192.168.10.31",
        mac_cisco: "00:27:0D:A1:B2:C7",
        modelo: "Cisco CP-7821",
        status: "ONLINE",
        latencia_ms: 11,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 108,
        numero: "2030",
        descricao: "Posto Maternidade 2º Andar",
        bloco: "Maternidade",
        setor: "Internação",
        ip: "192.168.10.40",
        mac_cisco: "00:27:0D:A1:B2:C8",
        modelo: "Cisco CP-3905",
        status: "ONLINE",
        latencia_ms: 18,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 109,
        numero: "2040",
        descricao: "Agendamento de Consultas - Ambulatório",
        bloco: "Ambulatório",
        setor: "Atendimento",
        ip: "192.168.10.50",
        mac_cisco: "00:27:0D:A1:B2:C9",
        modelo: "Cisco CP-7841",
        status: "ONLINE",
        latencia_ms: 22,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 110,
        numero: "2050",
        descricao: "TI - Central de Serviços e Telefonia",
        bloco: "Administrativo",
        setor: "Tecnologia da Informação",
        ip: "192.168.10.60",
        mac_cisco: "00:27:0D:A1:B2:CA",
        modelo: "Cisco CP-8861",
        status: "ONLINE",
        latencia_ms: 4,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
      {
        id: 111,
        numero: "2051",
        descricao: "Diretoria Clínica HAOC",
        bloco: "Administrativo",
        setor: "Diretoria",
        ip: "192.168.10.61",
        mac_cisco: "00:27:0D:A1:B2:CB",
        modelo: "Cisco CP-8845",
        status: "ONLINE",
        latencia_ms: 8,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      },
    ],
    incidentes: [
      {
        id: 1,
        ramal_id: 105,
        ramal_numero: "2011",
        ramal_descricao: "Coordenação Médica UTI",
        bloco: "UTI Geral",
        setor: "Coordenação",
        tipo: "QUEDA_TOTAL",
        gravidade: "ALTA",
        status: "ABERTO",
        aberto_em: new Date(Date.now() - 35 * 60000).toISOString(),
        resolvido_em: null,
        duracao_minutos: null,
        observacoes: "Equipamento não respondeu aos últimos 3 pacotes ICMP.",
      },
      {
        id: 2,
        ramal_id: 108,
        ramal_numero: "2030",
        ramal_descricao: "Posto Maternidade 2º Andar",
        bloco: "Maternidade",
        setor: "Internação",
        tipo: "ALTA_LATENCIA",
        gravidade: "MEDIA",
        status: "EM_ATENDIMENTO",
        aberto_em: new Date(Date.now() - 15 * 60000).toISOString(),
        resolvido_em: null,
        duracao_minutos: null,
        observacoes: "Latência média de 198ms acima do limiar de segurança (120ms).",
      },
    ],
    auditoria: [
      {
        id: 1,
        data_hora: new Date(Date.now() - 60 * 60000).toISOString(),
        usuario_nome: "Wagner (Administrador Master)",
        acao: "SISTEMA_INICIALIZADO",
        detalhes: "Núcleo corporativo HAOC VoIP Monitor Enterprise inicializado - Hospital Alemão Osvaldo Cruz.",
      },
      {
        id: 2,
        data_hora: new Date(Date.now() - 30 * 60000).toISOString(),
        usuario_nome: "Sistema (Monitor)",
        acao: "INCIDENTE_ABERTO",
        detalhes: "Detectada indisponibilidade no Ramal 2011 (UTI Geral).",
      },
    ],
  };
}

class Store {
  private data: DatabaseSchema;
  private networkConfig: NetworkSyncConfig;

  constructor() {
    this.data = this.load();
    // Garantir que todos os ramais sejam estritamente ONLINE ou OFFLINE
    for (const r of this.data.ramais) {
      if (r.status !== "OFFLINE") {
        r.status = "ONLINE";
      }
    }
    this.ensureMasterUser();
    this.save();

    // Carregar e tentar sincronizar automaticamente na inicialização a partir do caminho de rede
    this.networkConfig = this.loadNetworkConfig();
    if (this.networkConfig.auto_sync && this.networkConfig.caminho_rede) {
      console.log(`[Store] Inicializando busca do JSON na pasta de rede: ${this.networkConfig.caminho_rede}`);
      this.sincronizarCaminhoRede(this.networkConfig.caminho_rede);
    }
  }

  private loadNetworkConfig(): NetworkSyncConfig {
    const envPath = process.env.HAOC_NETWORK_JSON_PATH || process.env.NETWORK_JSON_PATH || "";
    const defaultCfg: NetworkSyncConfig = {
      caminho_rede: envPath,
      auto_sync: true,
      ultimo_sync: null,
      status: envPath ? "ERRO" : "NAO_CONFIGURADO",
      ultimo_erro: null,
      total_processados: 0,
    };
    try {
      if (fs.existsSync(NETWORK_CONFIG_PATH)) {
        const raw = fs.readFileSync(NETWORK_CONFIG_PATH, "utf-8");
        const parsed = JSON.parse(raw);
        return {
          ...defaultCfg,
          ...parsed,
          caminho_rede: parsed.caminho_rede || envPath,
        };
      }
    } catch (err) {
      console.warn("[Store] Erro ao ler network_config.json:", err);
    }
    return defaultCfg;
  }

  public saveNetworkConfig() {
    try {
      if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
      }
      fs.writeFileSync(NETWORK_CONFIG_PATH, JSON.stringify(this.networkConfig, null, 2), "utf-8");
    } catch (err) {
      console.error("[Store] Erro ao salvar network_config.json:", err);
    }
  }

  public getNetworkConfig(): NetworkSyncConfig {
    return { ...this.networkConfig };
  }

  public setNetworkConfig(caminho: string, autoSync: boolean = true): NetworkSyncConfig {
    this.networkConfig.caminho_rede = (caminho || "").trim();
    this.networkConfig.auto_sync = autoSync;
    this.saveNetworkConfig();
    if (this.networkConfig.caminho_rede) {
      this.sincronizarCaminhoRede(this.networkConfig.caminho_rede);
    }
    return { ...this.networkConfig };
  }

  public sincronizarCaminhoRede(caminhoEspecificado?: string): { sucesso: boolean; mensagem: string; detalhe?: any } {
    const alvo = (caminhoEspecificado || this.networkConfig.caminho_rede || "").trim();
    if (!alvo) {
      this.networkConfig.status = "NAO_CONFIGURADO";
      this.networkConfig.ultimo_erro = "Nenhum caminho de rede configurado.";
      this.saveNetworkConfig();
      return { sucesso: false, mensagem: "Nenhum caminho de rede configurado." };
    }

    try {
      let arquivoParaLer = alvo;
      if (!fs.existsSync(alvo)) {
        throw new Error(`Caminho de rede '${alvo}' não encontrado ou inacessível no momento.`);
      }

      const stat = fs.statSync(alvo);
      if (stat.isDirectory()) {
        const arquivos = fs.readdirSync(alvo).filter((f) => f.toLowerCase().endsWith(".json"));
        if (arquivos.length === 0) {
          throw new Error(`Nenhum arquivo .json encontrado na pasta de rede informada (${alvo}).`);
        }
        let escolhido = arquivos.find((f) => f.toLowerCase().includes("ramais") || f.toLowerCase().includes("haoc"));
        if (!escolhido) {
          escolhido = arquivos[0];
        }
        arquivoParaLer = path.join(alvo, escolhido);
      }

      const conteudoRaw = fs.readFileSync(arquivoParaLer, "utf-8");
      const parsed = JSON.parse(conteudoRaw);
      const resultado = this.importarJsonLegado(parsed, "AutoSync (Pasta de Rede)");

      this.networkConfig.caminho_rede = alvo;
      this.networkConfig.ultimo_sync = new Date().toISOString();
      this.networkConfig.status = "OK";
      this.networkConfig.ultimo_erro = null;
      this.networkConfig.total_processados = resultado.total;
      this.saveNetworkConfig();

      this.addLog("Sistema (AutoSync Rede)", "SINCRONIZACAO_REDE", `Sincronização com pasta de rede concluída a partir de ${path.basename(arquivoParaLer)}: ${resultado.inseridos} inseridos, ${resultado.atualizados} atualizados.`);

      return {
        sucesso: true,
        mensagem: `JSON de rede sincronizado com sucesso (${resultado.total} ramais ativos).`,
        detalhe: resultado,
      };
    } catch (err: any) {
      const msgErro = err.message || "Erro desconhecido ao acessar pasta de rede.";
      this.networkConfig.status = "ERRO";
      this.networkConfig.ultimo_erro = msgErro;
      this.saveNetworkConfig();
      console.warn(`[AutoSync Rede] Falha ao sincronizar de '${alvo}':`, msgErro);
      return { sucesso: false, mensagem: msgErro };
    }
  }

  private load(): DatabaseSchema {
    try {
      if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
      }
      if (fs.existsSync(DB_PATH)) {
        const raw = fs.readFileSync(DB_PATH, "utf-8");
        return JSON.parse(raw);
      }
    } catch (e) {
      console.warn("[Store] Falha ao carregar store.json, gerando dados padrão:", e);
    }
    const initial = getInitialData();
    this.persist(initial);
    return initial;
  }

  private persist(state: DatabaseSchema) {
    try {
      if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
      }
      fs.writeFileSync(DB_PATH, JSON.stringify(state, null, 2), "utf-8");
    } catch (err) {
      console.error("[Store] Erro ao persistir dados:", err);
    }
  }

  private save() {
    this.persist(this.data);
  }

  public ensureMasterUser() {
    let wagner = this.data.usuarios.find(
      (u) => u.login.toLowerCase() === "wagner"
    );
    if (!wagner) {
      wagner = {
        id: 1,
        nome: "Wagner (Administrador Master)",
        login: "Wagner",
        perfil: "ADMINISTRADOR",
        ativo: true,
        ultimo_login: null,
      };
      this.data.usuarios.unshift(wagner);
      this.save();
    } else {
      wagner.perfil = "ADMINISTRADOR";
      wagner.ativo = true;
      if (!wagner.nome.includes("Wagner")) {
        wagner.nome = "Wagner (Administrador Master)";
      }
      this.save();
    }
  }

  public autenticar(loginInput: string, senhaInput: string): Usuario | null {
    const loginClean = loginInput.trim().toLowerCase();
    const hash = hashPassword(senhaInput.trim());

    if (SENHAS_MAP[loginClean] && SENHAS_MAP[loginClean] === hash) {
      const u = this.data.usuarios.find((x) => x.login.toLowerCase() === loginClean);
      if (u && u.ativo) {
        u.ultimo_login = new Date().toISOString();
        this.addLog(u.nome, "LOGIN_EFETUADO", `Login bem-sucedido no perfil ${u.perfil}`);
        this.save();
        return u;
      }
    }
    return null;
  }

  public getStats() {
    const ramaisAtivos = this.data.ramais.filter((r) => r.ativo);
    const total = ramaisAtivos.length;
    const online = ramaisAtivos.filter((r) => r.status === "ONLINE").length;
    const offline = ramaisAtivos.filter((r) => r.status === "OFFLINE").length;
    const sla = total > 0 ? Number(((online / total) * 100).toFixed(1)) : 100.0;
    const incidentesAbertos = this.data.incidentes.filter((i) => i.status !== "RESOLVIDO").length;

    // Blocos
    const blocosMap: Record<string, { total: number; online: number; offline: number }> = {};
    for (const r of ramaisAtivos) {
      if (!blocosMap[r.bloco]) {
        blocosMap[r.bloco] = { total: 0, online: 0, offline: 0 };
      }
      blocosMap[r.bloco].total++;
      if (r.status === "ONLINE") blocosMap[r.bloco].online++;
      if (r.status === "OFFLINE") blocosMap[r.bloco].offline++;
    }

    return {
      total,
      online,
      offline,
      sla,
      incidentesAbertos,
      blocos: blocosMap,
    };
  }

  public getRamais(filtro?: { bloco?: string; status?: string; search?: string }) {
    let result = this.data.ramais.filter((r) => r.ativo);
    if (filtro?.bloco && filtro.bloco !== "TODOS") {
      result = result.filter((r) => r.bloco === filtro.bloco);
    }
    if (filtro?.status && filtro.status !== "TODOS") {
      result = result.filter((r) => r.status === filtro.status);
    }
    if (filtro?.search) {
      const q = filtro.search.toLowerCase();
      result = result.filter(
        (r) =>
          r.numero.toLowerCase().includes(q) ||
          r.descricao.toLowerCase().includes(q) ||
          r.ip.includes(q) ||
          r.mac_cisco.toLowerCase().includes(q) ||
          r.setor.toLowerCase().includes(q)
      );
    }

    // Ordenação: 1. OFFLINE primeiro (topo) | 2. Alfabética pela descrição
    result.sort((a, b) => {
      const aOff = a.status === "OFFLINE";
      const bOff = b.status === "OFFLINE";
      if (aOff && !bOff) return -1;
      if (!aOff && bOff) return 1;
      const cmpDesc = a.descricao.localeCompare(b.descricao, "pt-BR", { sensitivity: "base", numeric: true });
      if (cmpDesc !== 0) return cmpDesc;
      return a.numero.localeCompare(b.numero, "pt-BR", { numeric: true });
    });

    return result;
  }

  public getRamalById(id: number) {
    return this.data.ramais.find((r) => r.id === id && r.ativo);
  }

  public salvarRamal(novoRamal: Partial<Ramal>, usuarioNome: string): Ramal {
    if (novoRamal.id) {
      const idx = this.data.ramais.findIndex((r) => r.id === novoRamal.id);
      if (idx >= 0) {
        this.data.ramais[idx] = {
          ...this.data.ramais[idx],
          ...novoRamal,
        } as Ramal;
        this.addLog(usuarioNome, "RAMAL_ATUALIZADO", `Ramal ${this.data.ramais[idx].numero} editado.`);
        this.save();
        return this.data.ramais[idx];
      }
    }
    const maxId = this.data.ramais.reduce((acc, curr) => Math.max(acc, curr.id), 100);
    const criado: Ramal = {
      id: maxId + 1,
      numero: novoRamal.numero || "2000",
      descricao: novoRamal.descricao || "Novo Ramal VoIP",
      bloco: novoRamal.bloco || "Bloco Central",
      setor: novoRamal.setor || "Geral",
      ip: novoRamal.ip || "192.168.10.100",
      mac_cisco: novoRamal.mac_cisco || "00:27:0D:00:00:00",
      modelo: novoRamal.modelo || "Cisco CP-7841",
      status: "ONLINE",
      latencia_ms: 15,
      ultimo_ping: new Date().toISOString(),
      ativo: true,
      criado_em: new Date().toISOString(),
    };
    this.data.ramais.push(criado);
    this.addLog(usuarioNome, "RAMAL_CRIADO", `Novo ramal ${criado.numero} cadastrado no setor ${criado.setor}.`);
    this.save();
    return criado;
  }

  public desativarRamal(id: number, usuarioNome: string): boolean {
    const r = this.data.ramais.find((x) => x.id === id);
    if (r) {
      r.ativo = false;
      this.addLog(usuarioNome, "RAMAL_EXCLUIDO", `Ramal ${r.numero} (${r.descricao}) removido.`);
      this.save();
      return true;
    }
    return false;
  }

  public pingRamal(id: number): { status: string; latencia_ms: number } {
    const r = this.data.ramais.find((x) => x.id === id);
    if (!r) throw new Error("Ramal não encontrado");

    // Simulação determinística / ping check estritamente ONLINE ou OFFLINE
    const rdn = Math.random();
    if (rdn < 0.90) {
      r.status = "ONLINE";
      r.latencia_ms = Math.floor(Math.random() * 25) + 4;
    } else {
      r.status = "OFFLINE";
      r.latencia_ms = null;
    }
    r.ultimo_ping = new Date().toISOString();
    this.checkIncidente(r);
    this.save();
    return { status: r.status, latencia_ms: r.latencia_ms || 0 };
  }

  public pingAll(): { total: number; online: number; offline: number } {
    const ativos = this.data.ramais.filter((r) => r.ativo);
    let online = 0;
    let offline = 0;

    for (const r of ativos) {
      const rdn = Math.random();
      if (rdn < 0.90) {
        r.status = "ONLINE";
        r.latencia_ms = Math.floor(Math.random() * 20) + 5;
        online++;
      } else {
        r.status = "OFFLINE";
        r.latencia_ms = null;
        offline++;
      }
      r.ultimo_ping = new Date().toISOString();
      this.checkIncidente(r);
    }
    this.save();
    return { total: ativos.length, online, offline };
  }

  private checkIncidente(r: Ramal) {
    if (r.status === "OFFLINE") {
      const existeAberto = this.data.incidentes.find(
        (i) => i.ramal_id === r.id && i.status !== "RESOLVIDO"
      );
      if (!existeAberto) {
        const novoInc: Incidente = {
          id: this.data.incidentes.length + 1,
          ramal_id: r.id,
          ramal_numero: r.numero,
          ramal_descricao: r.descricao,
          bloco: r.bloco,
          setor: r.setor,
          tipo: "QUEDA_TOTAL",
          gravidade: r.bloco.includes("UTI") || r.bloco.includes("Cirúrgico") ? "CRITICA" : "ALTA",
          status: "ABERTO",
          aberto_em: new Date().toISOString(),
          resolvido_em: null,
          duracao_minutos: null,
          observacoes: "Dispositivo parou de responder durante monitoramento automatizado.",
        };
        this.data.incidentes.unshift(novoInc);
        this.addLog("Monitor Automático", "INCIDENTE_GERADO", `Falha detectada no ramal ${r.numero} (${r.bloco})`);
      }
    } else if (r.status === "ONLINE") {
      const incAberto = this.data.incidentes.find(
        (i) => i.ramal_id === r.id && i.status !== "RESOLVIDO"
      );
      if (incAberto) {
        incAberto.status = "RESOLVIDO";
        incAberto.resolvido_em = new Date().toISOString();
        const diffMs = new Date(incAberto.resolvido_em).getTime() - new Date(incAberto.aberto_em).getTime();
        incAberto.duracao_minutos = Math.max(1, Math.round(diffMs / 60000));
        this.addLog("Monitor Automático", "INCIDENTE_RESOLVIDO", `Ramal ${r.numero} restabelecido (Duração: ${incAberto.duracao_minutos} min).`);
      }
    }
  }

  public getIncidentes() {
    return this.data.incidentes;
  }

  public resolverIncidente(id: number, usuarioNome: string): boolean {
    const inc = this.data.incidentes.find((i) => i.id === id);
    if (inc) {
      inc.status = "RESOLVIDO";
      inc.resolvido_em = new Date().toISOString();
      const diffMs = new Date(inc.resolvido_em).getTime() - new Date(inc.aberto_em).getTime();
      inc.duracao_minutos = Math.max(1, Math.round(diffMs / 60000));
      this.addLog(usuarioNome, "INCIDENTE_BAIXADO_MANUAL", `Incidente #${id} do ramal ${inc.ramal_numero} baixado manualmente.`);
      this.save();
      return true;
    }
    return false;
  }

  public getAuditoria() {
    return this.data.auditoria.slice(0, 50);
  }

  public addLog(usuarioNome: string, acao: string, detalhes: string) {
    this.data.auditoria.unshift({
      id: this.data.auditoria.length + 1,
      data_hora: new Date().toISOString(),
      usuario_nome: usuarioNome,
      acao,
      detalhes,
    });
  }

  public getUsuarios() {
    return this.data.usuarios.map((u) => ({
      id: u.id,
      nome: u.nome,
      login: u.login,
      perfil: u.perfil,
      ativo: u.ativo,
      ultimo_login: u.ultimo_login,
    }));
  }

  public importarJsonLegado(input: any, usuarioNome: string) {
    let inseridos = 0;
    let atualizados = 0;

    let listaRaw: Array<{ item: any; blocoPadrao?: string }> = [];

    if (Array.isArray(input)) {
      listaRaw = input.map((it) => ({ item: it }));
    } else if (typeof input === "object" && input !== null) {
      if (Array.isArray(input.ramais)) {
        listaRaw = input.ramais.map((it: any) => ({ item: it }));
      } else if (Array.isArray(input.itens)) {
        listaRaw = input.itens.map((it: any) => ({ item: it }));
      } else {
        // Formato estruturado por Blocos: { "Bloco A": [...], "Bloco B": [...] }
        for (const [chaveBloco, valLista] of Object.entries(input)) {
          if (Array.isArray(valLista)) {
            for (const it of valLista) {
              listaRaw.push({ item: it, blocoPadrao: chaveBloco });
            }
          }
        }
      }
    }

    for (const { item, blocoPadrao } of listaRaw) {
      if (!item || typeof item !== "object") continue;

      const modelo = item["Modelo"] || item["modelo"] || "Cisco 7841";
      const descricao = item["Descrição"] || item["Descricao"] || item["descricao"] || "";
      const rawCisco = item["I.P Cisco"] || item["MAC Cisco"] || item["mac_cisco"] || item["mac"] || "";
      const rawIp = item["I.P"] || item["ip"] || item["IP"] || "";

      // Tratar "None" / "null" / "-" como sem IP (Status Offline)
      const isNoneIp = !rawIp || String(rawIp).trim().toLowerCase() === "none" || String(rawIp).trim() === "-";
      const ip = isNoneIp ? "" : String(rawIp).trim();

      // Extração inteligente do número do ramal
      let num = String(item["numero"] || item["ramal"] || "").trim();
      if (!num && descricao) {
        const matchFim = descricao.match(/(?:-\s*|\b)(\d{3,5})\s*$/);
        const matchIni = descricao.match(/^\s*(\d{3,5})\b/);
        const matchAny = descricao.match(/\b(\d{3,5})\b/);
        if (matchFim) num = matchFim[1];
        else if (matchIni) num = matchIni[1];
        else if (matchAny) num = matchAny[1];
      }

      if (!num) continue;

      // Normalização de MAC / SEP / CSF
      let mac = "";
      const ciscoStr = String(rawCisco).trim();
      if (ciscoStr.toUpperCase().startsWith("SEP") && ciscoStr.length === 15) {
        const hex = ciscoStr.slice(3).toUpperCase();
        mac = hex.match(/.{1,2}/g)?.join(":") || hex;
      } else if (ciscoStr.toUpperCase().startsWith("CSF")) {
        mac = ciscoStr.toUpperCase();
      } else if (ciscoStr) {
        const clean = ciscoStr.replace(/[^0-9A-Fa-f]/g, "").toUpperCase();
        if (clean.length === 12) {
          mac = clean.match(/.{1,2}/g)?.join(":") || clean;
        } else {
          mac = ciscoStr;
        }
      }

      // Extração de Setor da descrição
      let setor = item["Setor"] || item["setor"] || "";
      if (!setor && descricao) {
        const partes = descricao.split(" - ").map((s: string) => s.trim()).filter(Boolean);
        if (partes.length >= 3) {
          const penultima = partes[partes.length - 2];
          if (/^\d+$/.test(penultima) && partes.length >= 4) {
            setor = partes[partes.length - 3];
          } else {
            setor = penultima;
          }
        } else if (partes.length === 2) {
          setor = /^\d+$/.test(partes[1]) ? partes[0] : partes[1];
        }
      }
      if (!setor) setor = "Geral";

      const bloco = item["Bloco"] || item["bloco"] || blocoPadrao || "Bloco Central";
      const status = ip ? "ONLINE" : "OFFLINE";

      const existente = this.data.ramais.find((r) => r.numero === num);
      if (existente) {
        existente.descricao = descricao || existente.descricao;
        existente.bloco = bloco;
        existente.setor = setor;
        existente.ip = ip;
        existente.mac_cisco = mac || rawCisco || existente.mac_cisco;
        existente.modelo = modelo;
        existente.status = status;
        existente.latencia_ms = status === "ONLINE" ? 14 : null;
        existente.ativo = true;
        atualizados++;
      } else {
        const maxId = this.data.ramais.reduce((acc, curr) => Math.max(acc, curr.id), 100);
        this.data.ramais.push({
          id: maxId + 1,
          numero: num,
          descricao: descricao || `Ramal ${num}`,
          bloco,
          setor,
          ip,
          mac_cisco: mac || rawCisco || "00:27:0D:00:00:00",
          modelo,
          status,
          latencia_ms: status === "ONLINE" ? 14 : null,
          ultimo_ping: new Date().toISOString(),
          ativo: true,
          criado_em: new Date().toISOString(),
        });
        inseridos++;
      }
    }

    this.addLog(usuarioNome, "IMPORTACAO_JSON", `Importação concluída: ${inseridos} inseridos, ${atualizados} atualizados.`);
    this.save();
    return { inseridos, atualizados, total: this.data.ramais.filter((r) => r.ativo).length };
  }

  public exportarJsonModelo(): Record<string, any[]> {
    const ativos = this.data.ramais.filter((r) => r.ativo);
    const res: Record<string, any[]> = {};

    for (const r of ativos) {
      const blk = r.bloco || "Bloco Central";
      if (!res[blk]) res[blk] = [];

      let ciscoId = r.mac_cisco || "";
      const cleanHex = (r.mac_cisco || "").replace(/[^0-9A-Fa-f]/g, "").toUpperCase();
      if (r.mac_cisco && r.mac_cisco.toUpperCase().startsWith("CSF")) {
        ciscoId = r.mac_cisco.toUpperCase();
      } else if (cleanHex.length === 12) {
        ciscoId = `SEP${cleanHex}`;
      }

      res[blk].push({
        "Modelo": r.modelo || "Cisco 7841",
        "I.P Cisco": ciscoId,
        "Descrição": r.descricao,
        "I.P": r.ip && r.status === "ONLINE" ? r.ip : (r.ip || "None"),
      });
    }

    return res;
  }
}

export const store = new Store();
