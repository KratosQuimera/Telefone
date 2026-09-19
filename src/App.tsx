import React, { useState, useEffect, useMemo } from "react";
import { 
  Search, 
  RefreshCw, 
  Building2, 
  CheckCircle2, 
  XCircle, 
  PhoneCall,
  PackageCheck,
  ShieldAlert
} from "lucide-react";
import { Ramal, Incidente, Stats, Usuario, LogAuditoria } from "./types";
import { Navbar } from "./components/Navbar";
import { StatsBar } from "./components/StatsBar";
import { RamalCard } from "./components/RamalCard";
import { RamalModal } from "./components/RamalModal";
import { ImportModal } from "./components/ImportModal";
import { IncidentesModal } from "./components/IncidentesModal";
import { NetworkModal } from "./components/NetworkModal";
import { LoginModal } from "./components/LoginModal";
import { AuditoriaModal } from "./components/AuditoriaModal";
import { ModalExcluir } from "./components/ModalExcluir";
import { Network } from "lucide-react";

export default function App() {
  // Inicialização SEM senha na inicialização (Modo Livre / Monitoramento de Sala)
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  const [ramais, setRamais] = useState<Ramal[]>([]);
  const [stats, setStats] = useState<Stats>({
    total: 0,
    online: 0,
    offline: 0,
    sla: 100,
    incidentesAbertos: 0,
    blocos: {},
  });
  const [incidentes, setIncidentes] = useState<Incidente[]>([]);
  const [auditoriaLogs, setAuditoriaLogs] = useState<LogAuditoria[]>([]);

  // Filtros (Estritamente TODOS, ONLINE ou OFFLINE)
  const [blocoSelecionado, setBlocoSelecionado] = useState<string>("TODOS");
  const [statusFiltro, setStatusFiltro] = useState<string>("TODOS");
  const [busca, setBusca] = useState<string>("");

  // Modais
  const [modalRamalOpen, setModalRamalOpen] = useState(false);
  const [ramalEditar, setRamalEditar] = useState<Ramal | null>(null);
  const [ramalExcluir, setRamalExcluir] = useState<Ramal | null>(null);
  const [modalImportOpen, setModalImportOpen] = useState(false);
  const [modalIncidentesOpen, setModalIncidentesOpen] = useState(false);
  const [modalNetworkOpen, setModalNetworkOpen] = useState(false);
  const [modalLoginOpen, setModalLoginOpen] = useState(false);
  const [modalAuditoriaOpen, setModalAuditoriaOpen] = useState(false);

  // Controle de Acesso a Áreas Sensíveis
  const [motivoAcesso, setMotivoAcesso] = useState<string | null>(null);
  const [acaoPendente, setAcaoPendente] = useState<(() => void) | null>(null);

  // Estados de Operação e Varredura Otimizada
  const [loading, setLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState<{
    loteAtual: number;
    totalLotes: number;
    percentual: number;
    ramaisProcessados: number;
    totalRamais: number;
  } | null>(null);

  // Interceptor de Áreas Sensíveis (Solicita senha SOMENTE quando necessário)
  const executarAcaoSensivel = (motivo: string, acao: () => void) => {
    if (usuario && usuario.perfil === "ADMINISTRADOR") {
      acao();
    } else {
      setMotivoAcesso(motivo);
      setAcaoPendente(() => acao);
      setModalLoginOpen(true);
    }
  };

  const handleLoginSuccess = (u: Usuario) => {
    setUsuario(u);
    setModalLoginOpen(false);
    if (acaoPendente) {
      const run = acaoPendente;
      setAcaoPendente(null);
      setMotivoAcesso(null);
      run();
    }
  };

  // Carregar dados da API
  const carregarDados = async () => {
    try {
      const [resRamais, resStats, resIncidentes, resAuditoria] = await Promise.all([
        fetch("/api/ramais"),
        fetch("/api/stats"),
        fetch("/api/incidentes"),
        fetch("/api/auditoria"),
      ]);

      if (resRamais.ok) setRamais(await resRamais.json());
      if (resStats.ok) setStats(await resStats.json());
      if (resIncidentes.ok) setIncidentes(await resIncidentes.json());
      if (resAuditoria.ok) setAuditoriaLogs(await resAuditoria.json());
    } catch (e) {
      console.error("Erro ao carregar dados do servidor:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarDados();
    const interval = setInterval(carregarDados, 15000); // Atualização periódica
    return () => clearInterval(interval);
  }, []);

  // Ping em lotes (Dividido para não sobrecarregar memória da máquina e não atrapalhar o processamento)
  const handlePingAll = async () => {
    const ativos = ramais.filter((r) => r.ativo);
    if (ativos.length === 0) return;

    setIsScanning(true);
    // Divisão em lotes gerenciáveis (15 por vez) para manter baixa pegada de memória e CPU
    const BATCH_SIZE = 15;
    const lotes: Ramal[][] = [];
    for (let i = 0; i < ativos.length; i += BATCH_SIZE) {
      lotes.push(ativos.slice(i, i + BATCH_SIZE));
    }

    try {
      for (let i = 0; i < lotes.length; i++) {
        const lote = lotes[i];
        const ids = lote.map((r) => r.id);

        setScanProgress({
          loteAtual: i + 1,
          totalLotes: lotes.length,
          percentual: Math.round(((i + 1) / lotes.length) * 100),
          ramaisProcessados: Math.min((i + 1) * BATCH_SIZE, ativos.length),
          totalRamais: ativos.length,
        });

        const res = await fetch("/api/ramais/ping-lote", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ids }),
        });

        if (res.ok) {
          const data = await res.json();
          if (data.resultados && Array.isArray(data.resultados)) {
            const mapRes = new Map<number, { status: "ONLINE" | "OFFLINE"; latencia_ms: number | null }>();
            data.resultados.forEach((item: any) => {
              mapRes.set(item.id, { status: item.status, latencia_ms: item.latencia_ms });
            });

            // Atualização progressiva sem bloquear a renderização nem travar a máquina
            setRamais((prev) =>
              prev.map((r) => {
                const up = mapRes.get(r.id);
                if (up) {
                  return {
                    ...r,
                    status: up.status,
                    latencia_ms: up.latencia_ms,
                    ultimo_ping: new Date().toISOString(),
                  };
                }
                return r;
              })
            );
          }
        }

        // Pausa breve de 100ms para liberação de memória no ciclo de eventos
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      // Ao finalizar todos os lotes, recarrega estatísticas e incidentes globais
      await carregarDados();
    } catch (err) {
      console.error("Erro durante a varredura em lotes:", err);
    } finally {
      setIsScanning(false);
      setScanProgress(null);
    }
  };

  // Ping individual (Ação Livre de monitoramento)
  const handlePingRamal = async (id: number) => {
    try {
      const res = await fetch(`/api/ramais/${id}/ping`, { method: "POST" });
      if (res.ok) {
        await carregarDados();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Salvar Ramal (Área Sensível) com teste de ping imediato e atualização ordenada
  const handleSalvarRamal = async (dados: Partial<Ramal>) => {
    try {
      const res = await fetch("/api/ramais", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ramal: dados,
          usuario_nome: usuario?.nome || "Wagner",
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.erro || "Falha ao salvar ramal.");
      }
      const data = await res.json();
      
      // Se a API retornou a lista de ramais já atualizada e com ping testado, sincronizar o estado
      if (Array.isArray(data.ramais)) {
        setRamais(data.ramais);
      }
      if (data.stats) {
        setStats(data.stats);
      }
      
      // Sincronizar todos os dados do sistema
      await carregarDados();
    } catch (err: any) {
      console.error("Erro ao salvar ramal:", err);
      throw err;
    }
  };

  // Excluir Ramal e atualizar arquivos JSON
  const handleConfirmarExclusao = async (id: number) => {
    const alvo = ramais.find((r) => String(r.id) === String(id) || String(r.numero) === String(id));
    const targetId = alvo?.id ?? id;
    const numAlvo = alvo?.numero;

    // 1. Atualização visual instantânea na lista
    setRamais((prev) => prev.filter((r) => String(r.id) !== String(targetId) && (!numAlvo || String(r.numero) !== String(numAlvo))));
    setRamalExcluir(null);

    // 2. Enviar requisição DELETE ao servidor
    try {
      const res = await fetch(`/api/ramais/${targetId}?usuario_nome=${encodeURIComponent(usuario?.nome || "Wagner")}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: targetId,
          numero: alvo?.numero,
          descricao: alvo?.descricao,
          ip: alvo?.ip,
          mac_cisco: alvo?.mac_cisco,
          usuario_nome: usuario?.nome || "Wagner",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.ramais && Array.isArray(data.ramais)) {
          setRamais(data.ramais);
        }
        if (data.stats) {
          setStats(data.stats);
        }
      }
    } catch (err: any) {
      console.error("Erro ao excluir ramal:", err);
    } finally {
      // 3. Atualizar a lista automaticamente após exclusão
      await carregarDados();
    }
  };

  // Importar JSON (Área Sensível)
  const handleImportar = async (itens: any[]) => {
    const res = await fetch("/api/importar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        itens,
        usuario_nome: usuario?.nome || "Wagner",
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.erro || "Erro na importação.");
    }
    const data = await res.json();
    await carregarDados();
    return data;
  };

  // Resolver Incidente (Área Sensível)
  const handleResolverIncidente = async (id: number) => {
    const res = await fetch(`/api/incidentes/${id}/resolver`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ usuario_nome: usuario?.nome || "Wagner" }),
    });
    if (res.ok) {
      await carregarDados();
    }
  };

  // Exportar JSON oficial por Blocos
  const handleExportarJson = () => {
    window.location.href = "/api/exportar-json";
  };

  // Lista de Blocos únicos para o filtro
  const blocosDisponiveis = useMemo(() => {
    const set = new Set<string>();
    ramais.forEach((r) => set.add(r.bloco));
    return ["TODOS", ...Array.from(set)];
  }, [ramais]);

  // Filtragem e Ordenação Prioritária dos ramais em memória:
  // 1. Ramais OFFLINE aparecem no topo piscando para maior atenção
  // 2. Assim que o erro for sanado (ONLINE), voltam à sequência em ordem alfabética
  const ramaisFiltrados = useMemo(() => {
    return ramais
      .filter((r) => {
        if (!r) return false;
        if (blocoSelecionado !== "TODOS" && r.bloco !== blocoSelecionado) return false;
        if (statusFiltro !== "TODOS" && r.status !== statusFiltro) return false;
        if (busca.trim()) {
          const q = busca.toLowerCase();
          const num = String(r.numero || "").toLowerCase();
          const desc = String(r.descricao || "").toLowerCase();
          const ip = String(r.ip || "").toLowerCase();
          const mac = String(r.mac_cisco || "").toLowerCase();
          const setor = String(r.setor || "").toLowerCase();
          const match =
            num.includes(q) ||
            desc.includes(q) ||
            ip.includes(q) ||
            mac.includes(q) ||
            setor.includes(q);
          if (!match) return false;
        }
        return true;
      })
      .sort((a, b) => {
        const aOff = a?.status === "OFFLINE";
        const bOff = b?.status === "OFFLINE";

        // Se um estiver OFF e outro ON, o OFF tem prioridade máxima no topo
        if (aOff && !bOff) return -1;
        if (!aOff && bOff) return 1;

        // Se ambos estiverem com mesmo status (ou quando voltar a ser ONLINE), ordem alfabética estrita
        const descA = String(a?.descricao || "");
        const descB = String(b?.descricao || "");
        const cmpDesc = descA.localeCompare(descB, "pt-BR", { sensitivity: "base", numeric: true });
        if (cmpDesc !== 0) return cmpDesc;
        const numA = String(a?.numero || "");
        const numB = String(b?.numero || "");
        return numA.localeCompare(numB, "pt-BR", { numeric: true });
      });
  }, [ramais, blocoSelecionado, statusFiltro, busca]);

  const totalOfflineFiltrados = useMemo(() => {
    return ramaisFiltrados.filter((r) => r.status === "OFFLINE").length;
  }, [ramaisFiltrados]);

  return (
    <div className="min-h-screen bg-[#0a0e17] text-slate-100 flex flex-col antialiased">
      {/* Navbar Superior */}
      <Navbar
        usuario={usuario}
        onLogout={() => setUsuario(null)}
        onOpenLogin={() => {
          setMotivoAcesso("Autenticação Geral de Administrador");
          setAcaoPendente(null);
          setModalLoginOpen(true);
        }}
        onOpenNovoRamal={() => {
          executarAcaoSensivel("Cadastrar Novo Ramal VoIP", () => {
            setRamalEditar(null);
            setModalRamalOpen(true);
          });
        }}
        onOpenImport={() => {
          executarAcaoSensivel("Carregar Arquivo JSON de Ramais", () => {
            setModalImportOpen(true);
          });
        }}
        onExportJson={handleExportarJson}
        onOpenIncidentes={() => setModalIncidentesOpen(true)}
        onOpenAuditoria={() => {
          executarAcaoSensivel("Acessar Trilha de Auditoria e Logs do Sistema", () => {
            setModalAuditoriaOpen(true);
          });
        }}
        onOpenNetwork={() => setModalNetworkOpen(true)}
        onPingAll={handlePingAll}
        isScanning={isScanning}
        incidentesAbertos={stats.incidentesAbertos}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-2.5 sm:px-4 lg:px-6 py-4">
        {/* Banner Informativo Dark NOC */}
        <div className="mb-4 p-3.5 sm:p-4 rounded-xl bg-gradient-to-r from-[#0d131f] via-[#111827] to-[#162032] border border-slate-800 text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-extrabold tracking-tight text-white flex items-center gap-2">
                Hospital Alemão Osvaldo Cruz • NOC Telefonia IP
              </h2>
              <p className="text-[11px] text-slate-400">
                Monitoramento contínuo de ramais VoIP e integração automática com pasta de rede.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setModalNetworkOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a263d] hover:bg-[#223352] text-sky-300 text-xs font-semibold border border-sky-800/80 shadow-xs transition"
            >
              <Network className="w-3.5 h-3.5 text-sky-400" />
              <span>Pasta de Rede (JSON)</span>
            </button>
          </div>
        </div>

        {/* Barra de Estatísticas em Tempo Real */}
        <StatsBar stats={stats} />

        {/* Barra de Filtros e Busca Dark */}
        <div className="bg-[#111827] p-3 rounded-xl border border-slate-800 shadow-xs mb-4 space-y-2.5">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5">
            {/* Campo de Busca */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar por número, descrição, setor, IPv4 ou MAC..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="w-full text-xs pl-9 pr-8 py-2 bg-[#161f30] border border-slate-700/80 rounded-lg text-slate-100 placeholder:text-slate-500 focus:ring-1 focus:ring-emerald-500 focus:bg-[#1a2438] focus:outline-hidden transition font-sans"
              />
              {busca && (
                <button
                  onClick={() => setBusca("")}
                  className="absolute right-2.5 top-2 text-xs text-slate-400 hover:text-white"
                >
                  Limpar
                </button>
              )}
            </div>

            {/* Filtro por Status (Estritamente ONLINE ou OFFLINE) */}
            <div className="flex items-center gap-1 bg-[#161f30] p-1 rounded-lg shrink-0 text-xs font-semibold text-slate-300 border border-slate-700/60">
              <button
                onClick={() => setStatusFiltro("TODOS")}
                className={`px-2.5 py-1 rounded-md transition text-xs ${
                  statusFiltro === "TODOS" ? "bg-slate-800 text-white shadow-xs font-bold" : "hover:text-white"
                }`}
              >
                Todos ({ramais.length})
              </button>
              <button
                onClick={() => setStatusFiltro("ONLINE")}
                className={`px-2.5 py-1 rounded-md transition flex items-center gap-1 text-xs ${
                  statusFiltro === "ONLINE" ? "bg-emerald-600 text-white shadow-xs font-bold" : "hover:text-emerald-400"
                }`}
              >
                <CheckCircle2 className="w-3 h-3" />
                Online ({stats.online})
              </button>
              <button
                onClick={() => setStatusFiltro("OFFLINE")}
                className={`px-2.5 py-1 rounded-md transition flex items-center gap-1 text-xs ${
                  statusFiltro === "OFFLINE" ? "bg-rose-600 text-white shadow-xs font-bold" : "hover:text-rose-400"
                }`}
              >
                <XCircle className="w-3 h-3" />
                Offline ({stats.offline})
              </button>
            </div>
          </div>

          {/* Abas de Blocos Hospitalares */}
          <div className="flex items-center gap-1.5 overflow-x-auto pt-2 border-t border-slate-800/80 text-xs scrollbar-none">
            <span className="text-slate-400 font-semibold flex items-center gap-1 shrink-0 mr-1 text-[11px]">
              <Building2 className="w-3 h-3 text-slate-500" /> Bloco:
            </span>
            {blocosDisponiveis.map((bloco) => {
              const count = bloco === "TODOS" 
                ? ramais.length 
                : ramais.filter((r) => r.bloco === bloco).length;
              return (
                <button
                  key={bloco}
                  onClick={() => setBlocoSelecionado(bloco)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition whitespace-nowrap ${
                    blocoSelecionado === bloco
                      ? "bg-emerald-600 text-white font-bold shadow-xs"
                      : "bg-[#161f30] text-slate-300 hover:bg-slate-800 border border-slate-700/60"
                  }`}
                >
                  {bloco === "TODOS" ? "Todos os Blocos" : bloco} ({count})
                </button>
              );
            })}
          </div>
        </div>

        {/* Grade de Cartões de Ramais */}
        {loading ? (
          <div className="py-20 text-center">
            <RefreshCw className="w-8 h-8 text-emerald-500 animate-spin mx-auto mb-2" />
            <p className="text-xs text-slate-400 font-medium">Carregando ramais VoIP...</p>
          </div>
        ) : ramaisFiltrados.length === 0 ? (
          <div className="py-14 text-center bg-[#111827] rounded-xl border border-slate-800 p-6 shadow-xs">
            <PhoneCall className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-slate-200">Nenhum ramal encontrado</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Nenhum ramal corresponde aos critérios de busca ou filtros selecionados.
            </p>
            {(busca || blocoSelecionado !== "TODOS" || statusFiltro !== "TODOS") && (
              <button
                onClick={() => {
                  setBusca("");
                  setBlocoSelecionado("TODOS");
                  setStatusFiltro("TODOS");
                }}
                className="mt-3 px-3 py-1.5 bg-[#161f30] hover:bg-slate-800 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition"
              >
                Limpar Filtros
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {/* Banner de Progresso da Varredura em Lotes (Baixo consumo de CPU e Memória) */}
            {scanProgress && (
              <div className="bg-emerald-950/80 border border-emerald-600/80 rounded-xl p-3 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg shadow-emerald-950/40 text-xs">
                <div className="flex items-center gap-2.5 text-emerald-300">
                  <RefreshCw className="w-4 h-4 animate-spin text-emerald-400 shrink-0" />
                  <div>
                    <p className="font-bold text-white flex items-center gap-1.5">
                      <span>Varredura Dividida em Lotes</span>
                      <span className="text-[10px] bg-emerald-900 border border-emerald-700 px-1.5 py-0.2 rounded text-emerald-200">
                        Lote {scanProgress.loteAtual}/{scanProgress.totalLotes}
                      </span>
                    </p>
                    <p className="text-[11px] text-emerald-200/80">
                      Processando de modo escalonado ({scanProgress.ramaisProcessados}/{scanProgress.totalRamais} ramais) para poupar memória e processamento.
                    </p>
                  </div>
                </div>
                <div className="w-full sm:w-48 flex items-center gap-2">
                  <div className="flex-1 bg-slate-900 rounded-full h-2.5 overflow-hidden border border-emerald-800">
                    <div 
                      className="bg-emerald-400 h-full transition-all duration-300"
                      style={{ width: `${scanProgress.percentual}%` }}
                    />
                  </div>
                  <span className="font-bold font-mono text-white text-[11px] shrink-0">
                    {scanProgress.percentual}%
                  </span>
                </div>
              </div>
            )}

            {/* Aviso de Destaque no Topo para Ramais Offline */}
            {totalOfflineFiltrados > 0 && (
              <div className="bg-rose-950/40 border border-rose-800/80 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 offline-badge-blink shrink-0 shadow-xs shadow-rose-500" />
                  <p className="text-xs text-rose-200 font-medium leading-relaxed">
                    <strong className="text-rose-400 font-bold">{totalOfflineFiltrados} ramal(is) offline priorizado(s) no topo piscando</strong> para rápida resolução técnica.
                  </p>
                </div>
                <span className="self-start sm:self-auto text-[10px] font-extrabold text-rose-300 bg-rose-950 border border-rose-700 px-2 py-0.5 rounded uppercase tracking-wide shrink-0">
                  Prioridade NOC
                </span>
              </div>
            )}

            {/* Grid flexível e adaptativa: não corta cards em telas pequenas */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
              {ramaisFiltrados.map((ramal) => (
                <RamalCard
                  key={ramal.id}
                  ramal={ramal}
                  usuario={usuario}
                  onEdit={(r) => {
                    executarAcaoSensivel(`Editar Ramal ${r.numero}`, () => {
                      setRamalEditar(r);
                      setModalRamalOpen(true);
                    });
                  }}
                  onDelete={(r) => {
                    setRamalExcluir(r);
                  }}
                  onPing={handlePingRamal}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer corporativo Dark */}
      <footer className="bg-[#0d131f] border-t border-slate-800/80 py-3.5 text-center text-xs text-slate-400 mt-8">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>HAOC VoIP Enterprise • Hospital Alemão Osvaldo Cruz</span>
          <span>
            {usuario ? (
              <span className="text-emerald-400 font-semibold">
                Sessão Autenticada: {usuario.nome} ({usuario.perfil})
              </span>
            ) : (
              <span className="text-slate-400">
                Modo Monitoramento Aberto (NOC)
              </span>
            )}
          </span>
        </div>
      </footer>

      {/* Modais do Sistema */}
      <RamalModal
        isOpen={modalRamalOpen}
        onClose={() => {
          setModalRamalOpen(false);
          setRamalEditar(null);
        }}
        onSave={handleSalvarRamal}
        ramalEditar={ramalEditar}
      />

      <ImportModal
        isOpen={modalImportOpen}
        onClose={() => setModalImportOpen(false)}
        onImport={handleImportar}
      />

      <IncidentesModal
        isOpen={modalIncidentesOpen}
        onClose={() => setModalIncidentesOpen(false)}
        incidentes={incidentes}
        usuario={usuario}
        onResolver={(id) => {
          executarAcaoSensivel("Resolver Incidente Técnico", () => {
            handleResolverIncidente(id);
          });
          return Promise.resolve();
        }}
      />

      <NetworkModal
        isOpen={modalNetworkOpen}
        onClose={() => setModalNetworkOpen(false)}
        onSyncComplete={carregarDados}
      />

      <LoginModal
        isOpen={modalLoginOpen}
        onClose={() => {
          setModalLoginOpen(false);
          setMotivoAcesso(null);
          setAcaoPendente(null);
        }}
        onLoginSuccess={handleLoginSuccess}
        motivoAcesso={motivoAcesso}
      />

      <AuditoriaModal
        isOpen={modalAuditoriaOpen}
        onClose={() => setModalAuditoriaOpen(false)}
        logs={auditoriaLogs}
      />

      <ModalExcluir
        isOpen={!!ramalExcluir}
        ramal={ramalExcluir}
        onClose={() => setRamalExcluir(null)}
        onConfirm={handleConfirmarExclusao}
      />
    </div>
  );
}
