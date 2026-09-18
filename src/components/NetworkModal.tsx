import React, { useState, useEffect } from "react";
import { X, Network, Folder, RefreshCw, CheckCircle2, AlertCircle, HardDrive, ArrowRight, ShieldCheck } from "lucide-react";

interface NetworkModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSyncComplete?: () => void;
}

interface NetworkConfig {
  caminho_rede: string;
  auto_sync: boolean;
  ultimo_sync: string | null;
  status: "OK" | "ERRO" | "NAO_CONFIGURADO" | "PENDENTE";
  ultimo_erro: string | null;
  total_processados: number;
}

export const NetworkModal: React.FC<NetworkModalProps> = ({
  isOpen,
  onClose,
  onSyncComplete,
}) => {
  const [caminho, setCaminho] = useState("");
  const [autoSync, setAutoSync] = useState(true);
  const [config, setConfig] = useState<NetworkConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: "sucesso" | "erro"; texto: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      carregarConfig();
    }
  }, [isOpen]);

  const carregarConfig = async () => {
    setLoading(true);
    setMensagem(null);
    try {
      const res = await fetch("/api/rede/config");
      if (res.ok) {
        const data: NetworkConfig = await res.json();
        setConfig(data);
        setCaminho(data.caminho_rede || "");
        setAutoSync(data.auto_sync !== false);
      }
    } catch (e) {
      console.error("Erro ao ler configuração de rede:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSalvarConfig = async (executarSincronizacao = true) => {
    if (!caminho.trim()) {
      setMensagem({ tipo: "erro", texto: "Por favor, digite o caminho da pasta ou arquivo JSON na rede." });
      return;
    }

    setSyncing(true);
    setMensagem(null);

    try {
      // 1. Salva caminho e opção de auto sync
      const resSave = await fetch("/api/rede/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ caminho: caminho.trim(), auto_sync: autoSync }),
      });
      const dataCfg = await resSave.json();
      setConfig(dataCfg);

      if (executarSincronizacao) {
        // 2. Dispara sincronização imediata
        const resSync = await fetch("/api/rede/sincronizar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ caminho: caminho.trim() }),
        });
        const dataSync = await resSync.json();

        if (dataSync.sucesso) {
          setMensagem({ tipo: "sucesso", texto: dataSync.mensagem || "Sincronização concluída com sucesso!" });
          if (onSyncComplete) onSyncComplete();
          await carregarConfig();
        } else {
          setMensagem({ tipo: "erro", texto: dataSync.mensagem || "Não foi possível sincronizar o arquivo no caminho indicado." });
        }
      } else {
        setMensagem({ tipo: "sucesso", texto: "Caminho salvo com sucesso. O sistema buscará o arquivo a cada inicialização." });
      }
    } catch (err: any) {
      setMensagem({ tipo: "erro", texto: err.message || "Falha na comunicação com o servidor." });
    } finally {
      setSyncing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
      <div className="bg-[#111827] border border-slate-700 rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden flex flex-col text-slate-100">
        {/* Header */}
        <div className="bg-[#0b0f19] border-b border-slate-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Sincronização com Pasta de Rede (JSON)</h3>
              <p className="text-xs text-slate-400">Busca e carregamento automático ao iniciar o sistema</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto max-h-[80vh]">
          {/* Status Atual da Conexão */}
          <div className="p-3.5 rounded-xl bg-[#161f30] border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {config?.status === "OK" ? (
                <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              ) : config?.status === "ERRO" ? (
                <div className="w-9 h-9 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400">
                  <AlertCircle className="w-5 h-5" />
                </div>
              ) : (
                <div className="w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <HardDrive className="w-5 h-5" />
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-200">Status de Busca:</span>
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${
                      config?.status === "OK"
                        ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                        : config?.status === "ERRO"
                        ? "bg-rose-950 text-rose-300 border border-rose-800"
                        : "bg-amber-950 text-amber-300 border border-amber-800"
                    }`}
                  >
                    {config?.status === "OK"
                      ? "Conectado & Sincronizado"
                      : config?.status === "ERRO"
                      ? "Inacessível / Aguardando"
                      : "Não Configurado"}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {config?.ultimo_sync
                    ? `Última sincronização: ${new Date(config.ultimo_sync).toLocaleString("pt-BR")}`
                    : "Ainda não sincronizado a partir da rede"}
                </p>
              </div>
            </div>

            {config?.total_processados ? (
              <div className="text-right">
                <span className="text-lg font-extrabold text-emerald-400">{config.total_processados}</span>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Ramais</p>
              </div>
            ) : null}
          </div>

          {/* Mensagens de Feedback */}
          {mensagem && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                mensagem.tipo === "sucesso"
                  ? "bg-emerald-950/40 border-emerald-800/80 text-emerald-200"
                  : "bg-rose-950/40 border-rose-800/80 text-rose-200"
              }`}
            >
              {mensagem.tipo === "sucesso" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="flex-1">{mensagem.texto}</div>
            </div>
          )}

          {/* Campo de Caminho da Rede */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-300">
              Caminho da Pasta ou Arquivo JSON na Rede:
            </label>
            <div className="relative">
              <input
                type="text"
                value={caminho}
                onChange={(e) => setCaminho(e.target.value)}
                placeholder="Ex.: \\servidor\compartilhamento\ramais.json ou /caminho/rede/"
                className="w-full text-xs px-3 py-2.5 bg-[#1a2333] border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono"
              />
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Pode ser um arquivo direto (ex.: <code className="text-slate-300">\\servidor\ti\ramais.json</code>) ou uma pasta compartilhada. Se você apontar para uma pasta, o sistema localizará automaticamente os arquivos <code className="text-slate-300">.json</code> mais recentes ao iniciar.
            </p>
          </div>

          {/* Toggle de Auto-Sync no Startup */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-[#161f30] border border-slate-800">
            <div>
              <p className="text-xs font-bold text-slate-200">Sincronizar Automaticamente ao Iniciar</p>
              <p className="text-[11px] text-slate-400">
                Verifica a pasta de rede assim que o sistema ou o app desktop é aberto
              </p>
            </div>
            <input
              type="checkbox"
              checked={autoSync}
              onChange={(e) => setAutoSync(e.target.checked)}
              className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
            />
          </div>

          {/* Exemplos de uso rápido */}
          <div className="space-y-1.5">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Atalhos rápidos de teste:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setCaminho("data/modelo_ramais_haoc.json")}
                className="text-left p-2 rounded-lg bg-[#161f30] hover:bg-[#1f2b3e] border border-slate-800 text-[11px] text-slate-300 transition flex items-center justify-between"
              >
                <span>Modelo Oficial HAOC (Local)</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              </button>
              <button
                type="button"
                onClick={() => setCaminho("data/sample_legacy_data.json")}
                className="text-left p-2 rounded-lg bg-[#161f30] hover:bg-[#1f2b3e] border border-slate-800 text-[11px] text-slate-300 transition flex items-center justify-between"
              >
                <span>Base Legada Completa (Local)</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-[#0b0f19] border-t border-slate-800 px-6 py-4 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            Fechar
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={syncing || loading}
              onClick={() => handleSalvarConfig(false)}
              className="px-3.5 py-2 text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
            >
              Salvar Caminho
            </button>
            <button
              type="button"
              disabled={syncing || loading}
              onClick={() => handleSalvarConfig(true)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg shadow-md transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
              <span>{syncing ? "Sincronizando..." : "Sincronizar Agora"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
