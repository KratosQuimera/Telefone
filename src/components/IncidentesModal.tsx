import React from "react";
import { X, AlertTriangle, CheckCircle2, Clock, MapPin } from "lucide-react";
import { Incidente, Usuario } from "../types";

interface IncidentesModalProps {
  isOpen: boolean;
  onClose: () => void;
  incidentes: Incidente[];
  usuario: Usuario | null;
  onResolver: (id: number) => Promise<void>;
}

export const IncidentesModal: React.FC<IncidentesModalProps> = ({
  isOpen,
  onClose,
  incidentes,
  usuario,
  onResolver,
}) => {
  if (!isOpen) return null;

  const abertos = incidentes.filter((i) => i.status !== "RESOLVIDO");
  const resolvidos = incidentes.filter((i) => i.status === "RESOLVIDO");

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-3xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="font-bold text-base">
              Painel de Incidentes Hospitalares ({abertos.length} Pendentes)
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Seção de Abertos */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-600 mb-3 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              Incidentes em Aberto ({abertos.length})
            </h4>

            {abertos.length === 0 ? (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Nenhum incidente ativo no momento. Todos os ramais críticos estão operacionais!</span>
              </div>
            ) : (
              <div className="space-y-3">
                {abertos.map((inc) => (
                  <div
                    key={inc.id}
                    className="bg-rose-50/50 border border-rose-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">
                          Ramal {inc.ramal_numero} - {inc.ramal_descricao}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-200 text-rose-800 uppercase">
                          {inc.gravidade}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          {inc.bloco} - {inc.setor}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          Aberto às {new Date(inc.aberto_em).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1 italic">
                        "{inc.observacoes}"
                      </p>
                    </div>

                    <button
                      onClick={() => onResolver(inc.id)}
                      className="self-end sm:self-center px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition shadow-xs shrink-0"
                    >
                      Resolver Incidente
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Seção de Resolvidos Recentemente */}
          {resolvidos.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Histórico de Incidentes Resolvidos
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {resolvidos.map((inc) => (
                  <div
                    key={inc.id}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-bold text-slate-800 mr-2">Ramal {inc.ramal_numero}</span>
                      <span className="text-slate-600">{inc.ramal_descricao}</span>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Resolvido às {new Date(inc.resolvido_em!).toLocaleTimeString()} (Tempo de parada: {inc.duracao_minutos} min)
                      </div>
                    </div>
                    <span className="text-emerald-600 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Resolvido
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};
