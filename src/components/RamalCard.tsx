import React, { useState } from "react";
import { 
  Phone, 
  Wifi, 
  WifiOff, 
  MapPin, 
  Tag, 
  MoreVertical, 
  Edit, 
  Trash2, 
  RefreshCw,
  Cpu,
  AlertTriangle
} from "lucide-react";
import { Ramal, Usuario } from "../types";

interface RamalCardProps {
  ramal: Ramal;
  usuario: Usuario | null;
  onEdit: (ramal: Ramal) => void;
  onDelete: (ramal: Ramal) => void;
  onPing: (id: number) => Promise<void>;
}

export const RamalCard: React.FC<RamalCardProps> = ({
  ramal,
  usuario,
  onEdit,
  onDelete,
  onPing,
}) => {
  const [isPinging, setIsPinging] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const handlePing = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsPinging(true);
    try {
      await onPing(ramal.id);
    } finally {
      setIsPinging(false);
    }
  };

  const isOnline = ramal.status === "ONLINE";

  return (
    <div 
      className={`rounded-xl border transition-all p-3 relative flex flex-col justify-between min-w-0 min-h-[235px] h-full ${
        isOnline 
          ? "bg-[#111827] border-slate-800 hover:border-emerald-500/50 hover:bg-[#131b2c] shadow-xs" 
          : "offline-card-pulse border-rose-500/90 shadow-lg shadow-rose-950/50"
      }`}
    >
      <div className="min-w-0">
        {/* Banner de Alerta Chamativo para Ramal Offline (Mais compacto) */}
        {!isOnline && (
          <div className="mb-2 px-2 py-0.5 rounded bg-rose-600 text-white flex items-center justify-between shadow-xs">
            <span className="flex items-center gap-1 text-[10px] font-bold tracking-wide uppercase truncate">
              <AlertTriangle className="w-3 h-3 text-amber-300 offline-badge-blink shrink-0" />
              <span className="truncate">Falha Detectada</span>
            </span>
            <span className="offline-badge-blink text-[9px] font-extrabold bg-white text-rose-700 px-1 py-0.2 rounded shadow-xs uppercase shrink-0">
              Atenção
            </span>
          </div>
        )}

        {/* Top Header: Ramal & Status */}
        <div className="flex items-start justify-between gap-1.5 mb-1.5 min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            <div 
              className={`w-7 h-7 rounded-md flex items-center justify-center font-bold text-xs shrink-0 ${
                isOnline 
                  ? "bg-emerald-950/90 text-emerald-400 border border-emerald-800/80" 
                  : "bg-rose-950 text-rose-300 border border-rose-800 offline-badge-blink"
              }`}
            >
              <Phone className="w-3.5 h-3.5" />
            </div>
            <div className="min-w-0">
              <span className="font-extrabold text-white text-sm tracking-tight truncate block leading-none">
                Ramal {ramal.numero}
              </span>
              <p className="text-[10px] font-medium text-slate-400 flex items-center gap-1 mt-0.5 truncate">
                <Cpu className="w-2.5 h-2.5 text-slate-500 shrink-0" />
                <span className="truncate">{ramal.modelo || "Cisco 7841"}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <span 
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                isOnline 
                  ? "bg-emerald-950/80 text-emerald-300 border-emerald-800/80" 
                  : "bg-rose-950/80 text-rose-300 border-rose-800 ring-1 ring-rose-500/50"
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? "bg-emerald-400 animate-pulse" : "bg-rose-400 offline-badge-blink"}`} />
              {isOnline ? "Online" : "Offline"}
            </span>

            {/* Menu de ações */}
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
                title="Opções do ramal"
              >
                <MoreVertical className="w-3.5 h-3.5" />
              </button>
              {menuOpen && (
                <div 
                  onMouseLeave={() => setMenuOpen(false)}
                  className="absolute right-0 mt-1 w-28 bg-slate-900 rounded-lg shadow-xl border border-slate-700 py-1 z-20 text-xs"
                >
                  <button
                    onClick={() => { setMenuOpen(false); onEdit(ramal); }}
                    className="w-full text-left px-3 py-1.5 text-slate-200 hover:bg-slate-800 flex items-center gap-2"
                  >
                    <Edit className="w-3 h-3 text-emerald-400" /> Editar
                  </button>
                  <button
                    onClick={() => { setMenuOpen(false); onDelete(ramal); }}
                    className="w-full text-left px-3 py-1.5 text-rose-400 hover:bg-rose-950/40 flex items-center gap-2"
                  >
                    <Trash2 className="w-3 h-3 text-rose-400" /> Excluir
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Descrição em Exibição Completa (Sem cortes, fonte proporcional para acomodar até 3 linhas sem truncar) */}
        <div className="min-h-[46px] flex items-center mb-1.5">
          <h4 
            className={`font-semibold text-slate-200 break-words leading-tight w-full ${
              (ramal.descricao || "").length > 45
                ? "text-[10px] leading-[1.2]"
                : (ramal.descricao || "").length > 25
                ? "text-[11px] leading-[1.25]"
                : "text-xs leading-snug"
            }`}
            title={ramal.descricao}
          >
            {ramal.descricao || "Sem descrição"}
          </h4>
        </div>

        {/* Grade 2x2 compacta de informações detalhadas (Economiza espaço mantendo 100% das infos) */}
        <div className="grid grid-cols-2 gap-1.5 p-2 rounded-lg bg-[#0b0f19] border border-slate-800/90 text-[11px]">
          {/* Bloco */}
          <div className="min-w-0">
            <span className="text-slate-400 text-[10px] flex items-center gap-1 font-medium">
              <MapPin className="w-2.5 h-2.5 text-slate-500 shrink-0" /> Bloco
            </span>
            <span className="font-semibold text-slate-200 text-xs truncate block" title={ramal.bloco}>
              {ramal.bloco || "Geral"}
            </span>
          </div>

          {/* Setor */}
          <div className="min-w-0">
            <span className="text-slate-400 text-[10px] flex items-center gap-1 font-medium">
              <Tag className="w-2.5 h-2.5 text-slate-500 shrink-0" /> Setor
            </span>
            <span className="font-semibold text-slate-200 text-xs truncate block" title={ramal.setor}>
              {ramal.setor || "Geral"}
            </span>
          </div>

          {/* IP */}
          <div className="min-w-0">
            <span className="text-slate-400 text-[10px] font-medium block">IP</span>
            {ramal.ip && ramal.ip.trim() !== "None" && ramal.ip.trim() !== "" ? (
              <code className="font-mono text-[10px] text-emerald-400 bg-emerald-950/60 px-1 py-0.2 rounded border border-emerald-800/60 truncate block" title={ramal.ip}>
                {ramal.ip}
              </code>
            ) : (
              <span className="text-slate-400 text-[10px]">-</span>
            )}
          </div>

          {/* MAC Cisco */}
          <div className="min-w-0">
            <span className="text-slate-400 text-[10px] font-medium block">MAC Cisco</span>
            <code className="font-mono text-[10px] text-slate-300 truncate block" title={ramal.mac_cisco}>
              {ramal.mac_cisco || "-"}
            </code>
          </div>
        </div>
      </div>

      {/* Footer com Latência & Ping */}
      <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between min-w-0">
        <div className="flex items-center gap-1.5 text-[11px] min-w-0">
          {isOnline ? (
            <span className="text-emerald-400 font-semibold flex items-center gap-1 truncate">
              <Wifi className="w-3 h-3 text-emerald-400 shrink-0" />
              <span className="truncate">{ramal.latencia_ms ? `${ramal.latencia_ms}ms` : "Conectado"}</span>
            </span>
          ) : (
            <span className="text-rose-400 font-medium flex items-center gap-1 truncate">
              <WifiOff className="w-3 h-3 text-rose-400 shrink-0" />
              <span className="truncate">Indisponível</span>
            </span>
          )}
        </div>

        <button
          onClick={handlePing}
          disabled={isPinging}
          title="Testar resposta de ping"
          className="flex items-center gap-1 text-[10px] font-bold text-slate-300 hover:text-emerald-300 bg-[#1a2333] hover:bg-[#233147] px-2 py-0.5 rounded border border-slate-700 transition shrink-0"
        >
          <RefreshCw className={`w-2.5 h-2.5 ${isPinging ? "animate-spin text-emerald-400" : ""}`} />
          <span>{isPinging ? "..." : "Ping"}</span>
        </button>
      </div>
    </div>
  );
};
