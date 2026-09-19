import React, { useState } from "react";
import { Trash2, AlertTriangle, X, CheckCircle, FileText } from "lucide-react";
import { Ramal } from "../types";

interface ModalExcluirProps {
  isOpen: boolean;
  ramal: Ramal | null;
  onClose: () => void;
  onConfirm: (id: number) => Promise<void>;
}

export const ModalExcluir: React.FC<ModalExcluirProps> = ({
  isOpen,
  ramal,
  onClose,
  onConfirm,
}) => {
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  if (!isOpen || !ramal) return null;

  const handleExcluir = async () => {
    setLoading(true);
    setErro(null);
    try {
      await onConfirm(ramal.id);
      onClose();
    } catch (e: any) {
      setErro(e.message || "Falha ao excluir o ramal.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs">
      <div className="bg-[#0f172a] border border-rose-900/60 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header com destaque de perigo */}
        <div className="px-6 py-4 bg-gradient-to-r from-rose-950/70 to-slate-900 border-b border-rose-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-base">
            <Trash2 className="w-5 h-5 text-rose-500" />
            <span>Confirmar Exclusão de Ramal</span>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="flex items-start gap-3 p-3.5 bg-rose-950/30 border border-rose-800/40 rounded-xl text-xs text-rose-200 leading-relaxed">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-rose-100">Ação irreversível de exclusão</p>
              <p className="mt-1 text-slate-300">
                O ramal será removido do monitoramento em tempo real e a exclusão será aplicada diretamente nos arquivos <strong className="text-white">JSON do sistema e na pasta de rede</strong>.
              </p>
            </div>
          </div>

          {/* Dados do Ramal */}
          <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-4 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Número:</span>
              <span className="font-extrabold text-white text-sm bg-slate-800 px-2 py-0.5 rounded font-mono">
                Ramal {ramal.numero}
              </span>
            </div>
            <div className="flex items-start justify-between gap-2">
              <span className="text-slate-400 shrink-0">Descrição:</span>
              <span className="font-semibold text-slate-200 text-right break-words text-[11px]">
                {ramal.descricao}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Bloco / Setor:</span>
              <span className="text-slate-300 font-medium">
                {ramal.bloco} • {ramal.setor}
              </span>
            </div>
            {ramal.ip && (
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Endereço IP:</span>
                <code className="text-emerald-400 font-mono text-[11px]">
                  {ramal.ip}
                </code>
              </div>
            )}
          </div>

          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <FileText className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Modifica automaticamente os arquivos JSON correspondentes.</span>
          </div>

          {erro && (
            <div className="p-3 bg-rose-950/60 border border-rose-700/80 rounded-lg text-rose-300 text-xs font-semibold">
              {erro}
            </div>
          )}

          {/* Botões de Ação */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 transition"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleExcluir}
              disabled={loading}
              className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 active:bg-rose-700 shadow-md shadow-rose-950/50 transition flex items-center gap-2"
            >
              <Trash2 className="w-3.5 h-3.5" />
              {loading ? "Excluindo..." : "Excluir Ramal e Atualizar JSON"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
