import React from "react";
import { X, FileText, Clock, User, Shield } from "lucide-react";
import { LogAuditoria } from "../types";

interface AuditoriaModalProps {
  isOpen: boolean;
  onClose: () => void;
  logs: LogAuditoria[];
}

export const AuditoriaModal: React.FC<AuditoriaModalProps> = ({
  isOpen,
  onClose,
  logs,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-base">Trilha de Auditoria e Segurança</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-3">
          <p className="text-xs text-slate-500">
            Registro imutável de operações administrativas, alterações de ramais e incidentes registrados:
          </p>

          <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
            {logs.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                Nenhum log registrado ainda.
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="p-3 hover:bg-slate-50 transition text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-slate-800 flex items-center gap-1.5">
                      <Shield className="w-3.5 h-3.5 text-emerald-600" />
                      {log.acao}
                    </span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(log.data_hora).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-600 mb-1">{log.detalhes}</p>
                  <div className="text-[11px] text-slate-400 flex items-center gap-1">
                    <User className="w-3 h-3" />
                    Responsável: <strong className="text-slate-700">{log.usuario_nome}</strong>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white rounded-lg transition"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};
