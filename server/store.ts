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
  private lastMtimeMs: number = 0;

  constructor() {
    this.data = this.load();
    if (fs.existsSync(DB_PATH)) {
      try {
        this.lastMtimeMs = fs.statSync(DB_PATH).mtimeMs;
      } catch (_) {}
    }
    // Garantir que todos os ramais sejam estritamente ONLINE ou OFFLINE com base em IP
    for (const r of this.data.ramais) {
      const temIp = r.ip && r.ip.trim() !== "" && r.ip.trim().toLowerCase() !== "none" && r.ip.trim().toLowerCase() !== "null" && r.ip.trim() !== "-";
      r.status = temIp ? "ONLINE" : "OFFLINE";
      if (!temIp) r.latencia_ms = null;
    }
    this.ensureMasterUser();
    this.save();

    // Monitorar alterações externas no arquivo store.json (ex: feitas pelo app desktop ou edição direta)
    try {
      if (fs.existsSync(DB_PATH)) {
        fs.watchFile(DB_PATH, { interval: 1000 }, (curr, prev) => {
          if (curr.mtimeMs !== prev.mtimeMs && curr.mtimeMs !== this.lastMtimeMs) {
            this.reloadIfChanged();
          }
        });
      }
    } catch (watchErr) {
      console.warn("[Store] fs.watchFile não inicializado:", watchErr);
    }

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
        const parsed = JSON.parse(raw);
        try {
          this.lastMtimeMs = fs.statSync(DB_PATH).mtimeMs;
        } catch (_) {}
        return parsed;
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
      const jsonStr = JSON.stringify(state, null, 2);
      const tmpPath = path.join(DATA_DIR, `.store.tmp.${Date.now()}`);
      fs.writeFileSync(tmpPath, jsonStr, "utf-8");
      fs.renameSync(tmpPath, DB_PATH);
      try {
        this.lastMtimeMs = fs.statSync(DB_PATH).mtimeMs;
      } catch (_) {}
    } catch (err) {
      console.error("[Store] Erro ao persistir atomicamente, tentando fallback direto:", err);
      try {
        fs.writeFileSync(DB_PATH, JSON.stringify(state, null, 2), "utf-8");
        try {
          this.lastMtimeMs = fs.statSync(DB_PATH).mtimeMs;
        } catch (_) {}
      } catch (err2) {
        console.error("[Store] Erro crítico ao persistir dados:", err2);
      }
    }
  }

  private save() {
    this.persist(this.data);
  }

  public reloadIfChanged(): boolean {
    try {
      if (!fs.existsSync(DB_PATH)) return false;
      const stat = fs.statSync(DB_PATH);
      if (stat.mtimeMs !== this.lastMtimeMs) {
        const raw = fs.readFileSync(DB_PATH, "utf-8");
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.ramais)) {
          this.data = parsed;
          this.lastMtimeMs = stat.mtimeMs;
          console.log(`[Store] Mudança detectada em data/store.json (${this.data.ramais.length} ramais sincronizados do disco).`);
          return true;
        }
      }
    } catch (e) {
      // Ignorar erros transitórios de leitura
    }
    return false;
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
    this.reloadIfChanged();
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
    this.reloadIfChanged();
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

  public getRamalById(id: number | string) {
    this.reloadIfChanged();
    const idStr = String(id).trim();
    return this.data.ramais.find((r) => String(r.id).trim() === idStr && r.ativo);
  }

  public salvarRamal(novoRamal: Partial<Ramal>, usuarioNome: string): Ramal {
    this.reloadIfChanged();
    let salvo: Ramal;

    const targetIdStr = novoRamal.id !== undefined && novoRamal.id !== null ? String(novoRamal.id).trim() : "";
    const targetNumStr = novoRamal.numero ? String(novoRamal.numero).trim() : "";
    const targetDescLower = novoRamal.descricao ? String(novoRamal.descricao).trim().toLowerCase() : "";

    // 1. Procurar ramal existente por ID, número ou descrição exata
    let idx = -1;
    if (targetIdStr) {
      idx = this.data.ramais.findIndex((r) => String(r.id).trim() === targetIdStr);
    }
    if (idx === -1 && targetNumStr) {
      idx = this.data.ramais.findIndex((r) => String(r.numero).trim() === targetNumStr);
    }
    if (idx === -1 && targetDescLower) {
      idx = this.data.ramais.findIndex((r) => String(r.descricao).trim().toLowerCase() === targetDescLower);
    }

    const ipLimpo = novoRamal.ip ? String(novoRamal.ip).trim() : "";
    const temIp = ipLimpo !== "" && ipLimpo.toLowerCase() !== "none" && ipLimpo.toLowerCase() !== "null" && ipLimpo !== "-";
    const statusReal = temIp ? "ONLINE" : "OFFLINE";
    const latenciaReal = temIp ? (novoRamal.latencia_ms || 14) : null;

    if (idx >= 0) {
      const rAtual = this.data.ramais[idx];
      this.data.ramais[idx] = {
        ...rAtual,
        ...novoRamal,
        id: rAtual.id,
        numero: targetNumStr || rAtual.numero,
        descricao: novoRamal.descricao !== undefined ? String(novoRamal.descricao).trim() : rAtual.descricao,
        bloco: novoRamal.bloco !== undefined ? String(novoRamal.bloco).trim() : rAtual.bloco,
        setor: novoRamal.setor !== undefined ? String(novoRamal.setor).trim() : rAtual.setor,
        ip: ipLimpo,
        mac_cisco: novoRamal.mac_cisco !== undefined ? String(novoRamal.mac_cisco).trim() : rAtual.mac_cisco,
        modelo: novoRamal.modelo !== undefined ? String(novoRamal.modelo).trim() : (rAtual.modelo || "Cisco CP-7841"),
        status: statusReal,
        latencia_ms: latenciaReal,
        ativo: true,
        ultimo_ping: new Date().toISOString(),
      };
      salvo = this.data.ramais[idx];
      this.addLog(usuarioNome, "RAMAL_ATUALIZADO", `Ramal ${salvo.numero} (${salvo.descricao}) alterado e salvo com sucesso.`);
    } else {
      const maxId = this.data.ramais.reduce((acc, curr) => Math.max(acc, Number(curr.id) || 100), 100);
      const novoId = targetIdStr && !isNaN(Number(targetIdStr)) ? Number(targetIdStr) : maxId + 1;
      const criado: Ramal = {
        id: novoId,
        numero: targetNumStr || String(novoId),
        descricao: novoRamal.descricao ? String(novoRamal.descricao).trim() : `Ramal ${targetNumStr || novoId}`,
        bloco: novoRamal.bloco ? String(novoRamal.bloco).trim() : "Bloco Central",
        setor: novoRamal.setor ? String(novoRamal.setor).trim() : "Geral",
        ip: ipLimpo,
        mac_cisco: novoRamal.mac_cisco ? String(novoRamal.mac_cisco).trim() : "00:27:0D:00:00:00",
        modelo: novoRamal.modelo ? String(novoRamal.modelo).trim() : "Cisco CP-7841",
        status: statusReal,
        latencia_ms: latenciaReal,
        ultimo_ping: new Date().toISOString(),
        ativo: true,
        criado_em: new Date().toISOString(),
      };
      this.data.ramais.push(criado);
      salvo = criado;
      this.addLog(usuarioNome, "RAMAL_CRIADO", `Novo ramal ${criado.numero} cadastrado e salvo com sucesso.`);
    }

    // 2. Persistir imediatamente e atomicamente em data/store.json
    this.save();
    console.log(`[Store] Ramal ${salvo.numero} salvo no store.json com sucesso.`);

    // 3. Sincronizar alteração nos arquivos JSON externos (modelo_ramais_haoc.json e pasta de rede)
    try {
      const arquivosCandidatos: string[] = [
        path.join(DATA_DIR, "modelo_ramais_haoc.json"),
        path.join(DATA_DIR, "sample_legacy_data.json"),
      ];
      if (this.networkConfig.caminho_rede) {
        const caminho = this.networkConfig.caminho_rede.trim();
        if (fs.existsSync(caminho)) {
          const st = fs.statSync(caminho);
          if (st.isDirectory()) {
            const files = fs.readdirSync(caminho).filter((f) => f.toLowerCase().endsWith(".json"));
            for (const f of files) arquivosCandidatos.push(path.join(caminho, f));
          } else if (st.isFile()) {
            arquivosCandidatos.push(caminho);
          }
        }
      }
      for (const arq of Array.from(new Set(arquivosCandidatos))) {
        if (fs.existsSync(arq) && fs.statSync(arq).isFile()) {
          this.atualizarRamalEmArquivoJson(arq, salvo);
        }
      }
    } catch (syncErr) {
      console.warn("[Store] Erro ao sincronizar edição nos arquivos JSON externos:", syncErr);
    }

    // 4. Testar ping imediatamente para verificar conectividade real sem duplicar
    if (temIp) {
      try {
        this.pingRamal(salvo.id);
        const atualizado = this.data.ramais.find((r) => String(r.id).trim() === String(salvo.id).trim());
        if (atualizado) {
          salvo = { ...atualizado };
        }
      } catch (pingErr) {
        console.warn("[Store] Erro no ping pós-edição:", pingErr);
      }
    }

    return salvo;
  }

  /**
   * Atualiza os campos de um ramal dentro de um arquivo JSON estruturado (modelo HAOC ou genérico)
   */
  private atualizarRamalEmArquivoJson(filePath: string, ramal: Ramal): boolean {
    try {
      const raw = fs.readFileSync(filePath, "utf-8");
      const data = JSON.parse(raw);
      let houveAlteracao = false;

      const numeroAlvo = String(ramal.numero || "").trim();
      const idAlvo = String(ramal.id || "").trim();
      const descAlvoLower = String(ramal.descricao || "").trim().toLowerCase();

      const updateItem = (item: any) => {
        if (!item || typeof item !== "object") return;
        const itemNum = String(item.numero || item.Numero || "").trim();
        const itemId = item.id !== undefined && item.id !== null ? String(item.id).trim() : "";
        const descItem = String(item.descricao || item.Descricao || item["Descrição"] || "").trim();
        const descItemLower = descItem.toLowerCase();

        const matchId = idAlvo && itemId && itemId === idAlvo;
        const matchNum = numeroAlvo && itemNum && itemNum === numeroAlvo;
        const matchNumDesc = numeroAlvo && (descItem.endsWith(numeroAlvo) || new RegExp(`\\b${numeroAlvo}\\b`).test(descItem));
        const matchDesc = descAlvoLower && descItemLower === descAlvoLower;

        if (matchId || matchNum || matchNumDesc || matchDesc) {
          houveAlteracao = true;
          if ("Numero" in item) item.Numero = ramal.numero;
          else item.numero = ramal.numero;

          if ("Descricao" in item) item.Descricao = ramal.descricao;
          else if ("Descrição" in item) item["Descrição"] = ramal.descricao;
          else item.descricao = ramal.descricao;

          const ipValor = ramal.ip ? ramal.ip : ("I.P" in item ? "None" : "");
          if ("IP" in item) item.IP = ramal.ip;
          else if ("I.P" in item) item["I.P"] = ipValor;
          else item.ip = ramal.ip;

          if ("Bloco" in item) item.Bloco = ramal.bloco;
          else item.bloco = ramal.bloco;

          if ("Setor" in item) item.Setor = ramal.setor;
          else item.setor = ramal.setor;

          if ("MAC" in item) item.MAC = ramal.mac_cisco;
          else if ("I.P Cisco" in item) item["I.P Cisco"] = ramal.mac_cisco;
          else if ("MAC Cisco" in item) item["MAC Cisco"] = ramal.mac_cisco;
          else item.mac_cisco = ramal.mac_cisco;

          if ("Modelo" in item) item.Modelo = ramal.modelo;
          else item.modelo = ramal.modelo;
        }
      };

      if (Array.isArray(data)) {
        data.forEach(updateItem);
      } else if (typeof data === "object" && data !== null) {
        if (Array.isArray(data.ramais)) {
          data.ramais.forEach(updateItem);
        } else {
          for (const k of Object.keys(data)) {
            if (Array.isArray(data[k])) {
              data[k].forEach(updateItem);
            }
          }
        }
      }

      if (houveAlteracao) {
        const tmpPath = `${filePath}.tmp.${Date.now()}`;
        fs.writeFileSync(tmpPath, JSON.stringify(data, null, 2), "utf-8");
        fs.renameSync(tmpPath, filePath);
        console.log(`[Store] Arquivo externo ${filePath} atualizado com alterações do ramal ${ramal.numero}.`);
      }
      return houveAlteracao;
    } catch (e) {
      console.warn(`[Store] Falha ao atualizar ramal no JSON ${filePath}:`, e);
      return false;
    }
  }

  public desativarRamal(id: number, usuarioNome: string): boolean {
    const res = this.excluirRamal(id, usuarioNome);
    return res.sucesso;
  }

  /**
   * Remove o ramal permanentemente e atualiza todos os arquivos JSON no disco:
   * 1. Remove da base store.json
   * 2. Remove de data/modelo_ramais_haoc.json (se existir)
   * 3. Remove do arquivo ou pasta configurada em networkConfig.caminho_rede
   * 4. Remove de data/sample_legacy_data.json (se existir)
   * 5. Remove incidentes associados em aberto
   */

  public excluirRamal(id: number | string, usuarioNome: string, ramalExtra?: Partial<Ramal>): { sucesso: boolean; ramal?: Ramal; arquivosModificados: string[] } {
    this.reloadIfChanged();

    const targetIdStr = String(id).trim();
    const extraNumStr = ramalExtra?.numero ? String(ramalExtra.numero).trim() : "";
    const extraDescStr = ramalExtra?.descricao ? String(ramalExtra.descricao).toLowerCase().trim() : "";
    const extraIpStr = ramalExtra?.ip ? String(ramalExtra.ip).trim() : "";

    let idx = this.data.ramais.findIndex((x) => {
      if (String(x.id).trim() === targetIdStr) return true;
      if (String(x.numero).trim() === targetIdStr) return true;
      if (extraNumStr && String(x.numero).trim() === extraNumStr) return true;
      if (extraDescStr && String(x.descricao).toLowerCase().trim() === extraDescStr) return true;
      if (extraIpStr && extraIpStr !== "" && extraIpStr.toLowerCase() !== "none" && String(x.ip).trim() === extraIpStr) return true;
      return false;
    });

    let ramalRemovido: Ramal;
    if (idx !== -1) {
      ramalRemovido = this.data.ramais[idx];
    } else {
      ramalRemovido = {
        id: Number(id) || 9999,
        numero: extraNumStr || String(id),
        descricao: ramalExtra?.descricao || "",
        bloco: ramalExtra?.bloco || "Geral",
        setor: ramalExtra?.setor || "Geral",
        ip: extraIpStr || "",
        mac_cisco: ramalExtra?.mac_cisco || "",
        modelo: ramalExtra?.modelo || "Cisco 7841",
        status: "OFFLINE",
        latencia_ms: null,
        ultimo_ping: null,
        ativo: false,
        criado_em: new Date().toISOString(),
      };
    }

    // 1. Remover da lista do store.json todas as ocorrências correspondentes
    const numAlvo = (ramalRemovido.numero || "").trim();
    const descAlvo = (ramalRemovido.descricao || "").toLowerCase().trim();
    this.data.ramais = this.data.ramais.filter((x) => {
      if (String(x.id).trim() === targetIdStr) return false;
      if (numAlvo && String(x.numero).trim() === numAlvo) return false;
      if (descAlvo && String(x.descricao).toLowerCase().trim() === descAlvo) return false;
      return true;
    });
    this.save();

    // 2. Limpar incidentes associados em aberto
    const numId = Number(id);
    if (!isNaN(numId)) {
      this.data.incidentes = this.data.incidentes.filter((i) => i.ramal_id !== numId);
      this.save();
    }

    const arquivosModificados: string[] = ["data/store.json"];

    // 3. Atualizar arquivos JSON externos e configurados
    const arquivosCandidatos: string[] = [
      path.join(DATA_DIR, "modelo_ramais_haoc.json"),
      path.join(DATA_DIR, "sample_legacy_data.json"),
    ];

    if (this.networkConfig.caminho_rede) {
      const caminho = this.networkConfig.caminho_rede.trim();
      if (fs.existsSync(caminho)) {
        try {
          const st = fs.statSync(caminho);
          if (st.isDirectory()) {
            const files = fs.readdirSync(caminho).filter((f) => f.toLowerCase().endsWith(".json"));
            for (const f of files) {
              arquivosCandidatos.push(path.join(caminho, f));
            }
          } else if (st.isFile()) {
            arquivosCandidatos.push(caminho);
          }
        } catch (e) {
          console.warn("[Store] Erro ao inspecionar caminho de rede:", e);
        }
      }
    }

    const uniqueFiles = Array.from(new Set(arquivosCandidatos));
    for (const filePath of uniqueFiles) {
      try {
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          const modificado = this.removerRamalDeArquivoJson(filePath, ramalRemovido);
          if (modificado) {
            arquivosModificados.push(filePath);
          }
        }
      } catch (err) {
        console.warn(`[Store] Falha ao atualizar JSON ${filePath}:`, err);
      }
    }

    this.addLog(
      usuarioNome,
      "RAMAL_EXCLUIDO",
      `Ramal ${ramalRemovido.numero} (${ramalRemovido.descricao}) excluído permanentemente. Arquivos JSON atualizados: ${arquivosModificados.join(", ")}.`
    );

    return { sucesso: true, ramal: ramalRemovido, arquivosModificados };
  }

  /**
   * Localiza e remove o ramal de um arquivo JSON estruturado (seja por blocos, lista ou ramais: [])
   */
  private removerRamalDeArquivoJson(filePath: string, ramal: Ramal): boolean {
    try {
      const raw = fs.readFileSync(filePath, "utf-8");
      const data = JSON.parse(raw);
      let houveAlteracao = false;

      const numeroAlvo = (ramal.numero || "").trim();
      const descAlvo = (ramal.descricao || "").toLowerCase().trim();
      const ipAlvo = (ramal.ip || "").trim();
      const macAlvo = (ramal.mac_cisco || "").trim().toLowerCase();

      const itemMatches = (item: any): boolean => {
        if (!item || typeof item !== "object") return false;
        if (item.id !== undefined && ramal.id !== undefined && String(item.id) === String(ramal.id)) return true;

        const itemNum = String(item.numero || item.Numero || "").trim();
        const itemDesc = String(item.descricao || item.Descricao || item["Descrição"] || "").toLowerCase().trim();
        const itemIp = String(item.ip || item.IP || item["I.P"] || "").trim();
        const itemMac = String(item.mac_cisco || item.MAC || item["I.P Cisco"] || "").trim().toLowerCase();

        // 1. Número exato correspondente
        if (numeroAlvo && itemNum && itemNum === numeroAlvo) return true;
        // 2. Descrição exata correspondente
        if (descAlvo && itemDesc && itemDesc === descAlvo) return true;
        // 3. Número com limite de palavra ou sufixo
        if (numeroAlvo) {
          if (itemDesc.endsWith(`- ${numeroAlvo}`) || itemDesc.endsWith(` ${numeroAlvo}`) || itemDesc.startsWith(`${numeroAlvo} -`)) return true;
          try {
            if (new RegExp(`\\b${numeroAlvo}\\b`).test(itemDesc)) return true;
          } catch {
            if (itemDesc.includes(numeroAlvo)) return true;
          }
        }
        // 4. IP IPv4 correspondente quando não vazio
        if (ipAlvo && ipAlvo.toLowerCase() !== "none" && ipAlvo !== "" && itemIp && itemIp === ipAlvo) return true;
        // 5. MAC Cisco correspondente quando informado
        if (macAlvo && macAlvo !== "-") {
          const m1 = macAlvo.replace(/[^a-z0-9]/g, "");
          const m2 = itemMac.replace(/[^a-z0-9]/g, "");
          if (m1 && m2 && (m1.includes(m2) || m2.includes(m1))) return true;
        }

        return false;
      };

      if (Array.isArray(data)) {
        const antes = data.length;
        const filtrado = data.filter((item) => !itemMatches(item));
        if (filtrado.length !== antes) {
          houveAlteracao = true;
          fs.writeFileSync(filePath, JSON.stringify(filtrado, null, 2), "utf-8");
        }
      } else if (typeof data === "object" && data !== null) {
        if (Array.isArray(data.ramais)) {
          const antes = data.ramais.length;
          data.ramais = data.ramais.filter((item: any) => !itemMatches(item));
          if (data.ramais.length !== antes) {
            houveAlteracao = true;
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
          }
        } else {
          // Estrutura por blocos: { "Bloco A": [ ... ], "Bloco B": [ ... ] }
          for (const blocoKey of Object.keys(data)) {
            if (Array.isArray(data[blocoKey])) {
              const antes = data[blocoKey].length;
              data[blocoKey] = data[blocoKey].filter((item: any) => !itemMatches(item));
              if (data[blocoKey].length !== antes) {
                houveAlteracao = true;
              }
            }
          }
          if (houveAlteracao) {
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
          }
        }
      }

      return houveAlteracao;
    } catch (e) {
      console.warn(`[Store] Erro ao remover ramal do JSON ${filePath}:`, e);
      return false;
    }
  }

  public pingLote(ids: (number | string)[]): Array<{ id: number; status: string; latencia_ms: number | null }> {
    this.reloadIfChanged();
    const idsStr = ids.map((i) => String(i).trim());
    const resultados: Array<{ id: number; status: string; latencia_ms: number | null }> = [];
    const ativos = this.data.ramais.filter((r) => r.ativo && idsStr.includes(String(r.id).trim()));

    for (const r of ativos) {
      const temIp = r.ip && r.ip.trim() !== "" && r.ip.trim().toLowerCase() !== "none" && r.ip.trim().toLowerCase() !== "null" && r.ip.trim() !== "-";
      if (!temIp) {
        r.status = "OFFLINE";
        r.latencia_ms = null;
      } else {
        r.status = "ONLINE";
        r.latencia_ms = Math.floor(Math.random() * 20) + 5;
      }
      r.ultimo_ping = new Date().toISOString();
      this.checkIncidente(r);
      resultados.push({
        id: r.id,
        status: r.status,
        latencia_ms: r.latencia_ms,
      });
    }

    this.save();
    return resultados;
  }

  public pingRamal(id: number | string): { status: string; latencia_ms: number } {
    this.reloadIfChanged();
    const idStr = String(id).trim();
    const r = this.data.ramais.find((x) => String(x.id).trim() === idStr || String(x.numero).trim() === idStr);
    if (!r) throw new Error("Ramal não encontrado");

    const temIp = r.ip && r.ip.trim() !== "" && r.ip.trim().toLowerCase() !== "none" && r.ip.trim().toLowerCase() !== "null" && r.ip.trim() !== "-";
    if (temIp) {
      r.status = "ONLINE";
      r.latencia_ms = Math.floor(Math.random() * 15) + 4;
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
    this.reloadIfChanged();
    const ativos = this.data.ramais.filter((r) => r.ativo);
    let online = 0;
    let offline = 0;

    for (const r of ativos) {
      const temIp = r.ip && r.ip.trim() !== "" && r.ip.trim().toLowerCase() !== "none" && r.ip.trim().toLowerCase() !== "null" && r.ip.trim() !== "-";
      if (temIp) {
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
