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

export interface Stats {
  total: number;
  online: number;
  offline: number;
  sla: number;
  incidentesAbertos: number;
  blocos: Record<string, { total: number; online: number; offline: number }>;
}
