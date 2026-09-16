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
import { ExeModal } from "./components/ExeModal";
import { LoginModal } from "./components/LoginModal";
import { AuditoriaModal } from "./components/AuditoriaModal";

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
  const [modalImportOpen, setModalImportOpen] = useState(false);
  const [modalIncidentesOpen, setModalIncidentesOpen] = useState(false);
  const [modalExeOpen, setModalExeOpen] = useState(false);
  const [modalLoginOpen, setModalLoginOpen] = useState(false);
  const [modalAuditoriaOpen, setModalAuditoriaOpen] = useState(false);

  // Controle de Acesso a Áreas Sensíveis
  const [motivoAcesso, setMotivoAcesso] = useState<string | null>(null);
  const [acaoPendente, setAcaoPendente] = useState<(() => void) | null>(null);

  // Estados de Operação
  const [loading, setLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);

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

  // Ping em todos (Ação Livre de monitoramento)
  const handlePingAll = async () => {
    setIsScanning(true);
    try {
      const res = await fetch("/api/ping-all", { method: "POST" });
      if (res.ok) {
        await carregarDados();
      }
    } finally {
      setIsScanning(false);
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

  // Salvar Ramal (Área Sensível)
  const handleSalvarRamal = async (dados: Partial<Ramal>) => {
    const res = await fetch("/api/ramais", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ramal: dados,
        usuario_nome: usuario?.nome || "Wagner",
      }),
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.erro || "Falha ao salvar ramal.");
    }
    await carregarDados();
  };

  // Excluir Ramal (Área Sensível)
  const handleExcluirRamal = async (id: number) => {
    if (!confirm("Deseja realmente desativar este ramal do monitoramento?")) return;
    const res = await fetch(`/api/ramais/${id}?usuario_nome=${encodeURIComponent(usuario?.nome || "Wagner")}`, {
      method: "DELETE",
    });
    if (res.ok) {
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

  // Lista de Blocos únicos para o filtro
  const blocosDisponiveis = useMemo(() => {
    const set = new Set<string>();
    ramais.forEach((r) => set.add(r.bloco));
    return ["TODOS", ...Array.from(set)];
  }, [ramais]);

  // Filtragem dos ramais em memória (Estritamente ONLINE ou OFFLINE)
  const ramaisFiltrados = useMemo(() => {
    return ramais.filter((r) => {
      if (blocoSelecionado !== "TODOS" && r.bloco !== blocoSelecionado) return false;
      if (statusFiltro !== "TODOS" && r.status !== statusFiltro) return false;
      if (busca.trim()) {
        const q = busca.toLowerCase();
        const match =
          r.numero.toLowerCase().includes(q) ||
          r.descricao.toLowerCase().includes(q) ||
          r.ip.includes(q) ||
          r.mac_cisco.toLowerCase().includes(q) ||
          r.setor.toLowerCase().includes(q);
        if (!match) return false;
      }
      return true;
    });
  }, [ramais, blocoSelecionado, statusFiltro, busca]);

  return (
    <div className="min-h-screen bg-slate-100/70 text-slate-800 flex flex-col antialiased">
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
        onOpenIncidentes={() => setModalIncidentesOpen(true)}
        onOpenAuditoria={() => {
          executarAcaoSensivel("Acessar Trilha de Auditoria e Logs do Sistema", () => {
            setModalAuditoriaOpen(true);
          });
        }}
        onOpenExe={() => setModalExeOpen(true)}
        onPingAll={handlePingAll}
        isScanning={isScanning}
        incidentesAbertos={stats.incidentesAbertos}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Banner Informativo */}
        <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                Hospital Augusto de Oliveira Camargo • NOC Telefonia IP
              </h2>
              <p className="text-xs text-slate-300">
                Monitoramento ativo e transparente de ramais VoIP corporativos. Acesso livre para consulta e status em tempo real.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setModalExeOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-xs transition"
            >
              <PackageCheck className="w-3.5 h-3.5" />
              Baixar / Compilar .EXE
            </button>
          </div>
        </div>

        {/* Barra de Estatísticas em Tempo Real (Apenas Online / Offline) */}
        <StatsBar stats={stats} />

        {/* Barra de Filtros e Busca */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs mb-6 space-y-3">
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
            {/* Campo de Busca */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Buscar por número, descrição, setor, IPv4 ou MAC..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="w-full text-xs pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:bg-white focus:outline-hidden transition"
              />
              {busca && (
                <button
                  onClick={() => setBusca("")}
                  className="absolute right-3 top-2.5 text-xs text-slate-400 hover:text-slate-600"
                >
                  Limpar
                </button>
              )}
            </div>

            {/* Filtro por Status (Estritamente ONLINE ou OFFLINE) */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl shrink-0 text-xs font-semibold text-slate-600">
              <button
                onClick={() => setStatusFiltro("TODOS")}
                className={`px-3.5 py-1.5 rounded-lg transition ${
                  statusFiltro === "TODOS" ? "bg-white text-slate-900 shadow-xs" : "hover:text-slate-900"
                }`}
              >
                Todos ({ramais.length})
              </button>
              <button
                onClick={() => setStatusFiltro("ONLINE")}
                className={`px-3.5 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  statusFiltro === "ONLINE" ? "bg-emerald-600 text-white shadow-xs" : "hover:text-emerald-700"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Online ({stats.online})
              </button>
              <button
                onClick={() => setStatusFiltro("OFFLINE")}
                className={`px-3.5 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  statusFiltro === "OFFLINE" ? "bg-rose-600 text-white shadow-xs" : "hover:text-rose-700"
                }`}
              >
                <XCircle className="w-3.5 h-3.5" />
                Offline ({stats.offline})
              </button>
            </div>
          </div>

          {/* Abas de Blocos Hospitalares */}
          <div className="flex items-center gap-2 overflow-x-auto pt-2 border-t border-slate-100 text-xs scrollbar-none">
            <span className="text-slate-400 font-semibold flex items-center gap-1 shrink-0 mr-1">
              <Building2 className="w-3.5 h-3.5" /> Bloco:
            </span>
            {blocosDisponiveis.map((bloco) => {
              const count = bloco === "TODOS" 
                ? ramais.length 
                : ramais.filter((r) => r.bloco === bloco).length;
              return (
                <button
                  key={bloco}
                  onClick={() => setBlocoSelecionado(bloco)}
                  className={`px-3 py-1 rounded-lg font-medium transition whitespace-nowrap ${
                    blocoSelecionado === bloco
                      ? "bg-slate-900 text-white shadow-xs"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
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
            <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-2" />
            <p className="text-sm text-slate-500 font-medium">Carregando ramais VoIP...</p>
          </div>
        ) : ramaisFiltrados.length === 0 ? (
          <div className="py-16 text-center bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
            <PhoneCall className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h4 className="text-base font-bold text-slate-800">Nenhum ramal encontrado</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Nenhum ramal corresponde aos critérios de busca ou filtros selecionados.
            </p>
            {(busca || blocoSelecionado !== "TODOS" || statusFiltro !== "TODOS") && (
              <button
                onClick={() => {
                  setBusca("");
                  setBlocoSelecionado("TODOS");
                  setStatusFiltro("TODOS");
                }}
                className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition"
              >
                Limpar Todos os Filtros
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
                onDelete={(id) => {
                  executarAcaoSensivel("Excluir Ramal", () => {
                    handleExcluirRamal(id);
                  });
                }}
                onPing={handlePingRamal}
              />
            ))}
          </div>
        )}
      </main>

      {/* Footer corporativo */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500 mt-10">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>HAOC VoIP Monitor Enterprise v2.5 • Tecnologia da Informação HAOC</span>
          <span>
            {usuario ? (
              <span className="text-emerald-700 font-semibold">
                Sessão Autenticada: {usuario.nome} ({usuario.perfil})
              </span>
            ) : (
              <span className="text-slate-500">
                Modo Monitoramento Aberto (NOC) • Senha solicitada apenas em alterações
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

      <ExeModal
        isOpen={modalExeOpen}
        onClose={() => setModalExeOpen(false)}
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
    </div>
  );
}
