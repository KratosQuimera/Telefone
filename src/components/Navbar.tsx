import React from "react";
import { 
  PhoneCall, 
  Plus, 
  Upload, 
  Download,
  AlertTriangle, 
  Network, 
  ShieldCheck, 
  RefreshCw,
  FileText,
  Lock,
  Unlock
} from "lucide-react";
import { Usuario } from "../types";

interface NavbarProps {
  usuario: Usuario | null;
  onLogout: () => void;
  onOpenLogin: () => void;
  onOpenNovoRamal: () => void;
  onOpenImport: () => void;
  onExportJson?: () => void;
  onOpenIncidentes: () => void;
  onOpenAuditoria: () => void;
  onOpenNetwork: () => void;
  onPingAll: () => void;
  isScanning: boolean;
  incidentesAbertos: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  usuario,
  onLogout,
  onOpenLogin,
  onOpenNovoRamal,
  onOpenImport,
  onExportJson,
  onOpenIncidentes,
  onOpenAuditoria,
  onOpenNetwork,
  onPingAll,
  isScanning,
  incidentesAbertos,
}) => {
  const isAdmin = usuario?.perfil === "ADMINISTRADOR";

  return (
    <header className="bg-[#0d131f] border-b border-slate-800 text-white sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-2.5 sm:px-4 lg:px-6">
        <div className="flex items-center justify-between h-15 gap-2">
          {/* Brand */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center shadow-md">
              <PhoneCall className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base sm:text-lg tracking-tight text-white">HAOC VoIP</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold uppercase tracking-wider">
                  NOC
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden md:block">
                Hospital Alemão Osvaldo Cruz • Centro de Telefonia IP
              </p>
            </div>
          </div>

          {/* Actions: scrollable on ultra-narrow, neatly aligned on normal */}
          <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto py-1 scrollbar-none">
            {/* Ping Geral (Livre) */}
            <button
              onClick={onPingAll}
              disabled={isScanning}
              title="Disparar teste de conectividade em todos os ramais"
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0 ${
                isScanning 
                  ? "bg-slate-800 text-slate-400 cursor-not-allowed" 
                  : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-xs"
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">{isScanning ? "Varrendo..." : "Verificar"}</span>
            </button>

            {/* Sincronização Pasta de Rede */}
            <button
              onClick={onOpenNetwork}
              title="Configurar pasta de rede e auto-carregamento do JSON"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#162032] hover:bg-[#1f2d47] text-sky-300 text-xs font-semibold border border-sky-800/60 transition shrink-0"
            >
              <Network className="w-3.5 h-3.5 text-sky-400" />
              <span className="hidden md:inline">Pasta de Rede</span>
            </button>

            {/* Ações Administrativas / Sensíveis */}
            <button
              onClick={onOpenNovoRamal}
              title="Cadastrar novo ramal (Área Sensível)"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#161f30] hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700 transition shrink-0"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden lg:inline">Novo Ramal</span>
            </button>

            <button
              onClick={onOpenImport}
              title="Carregar arquivo .JSON (Área Sensível)"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#161f30] hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700 transition shrink-0"
            >
              <Upload className="w-3.5 h-3.5 text-slate-300" />
              <span className="hidden lg:inline">Importar</span>
            </button>

            {onExportJson && (
              <button
                onClick={onExportJson}
                title="Exportar base no formato oficial de Blocos"
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#161f30] hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700 transition shrink-0"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden lg:inline">Exportar</span>
              </button>
            )}

            <button
              onClick={onOpenIncidentes}
              className="relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#161f30] hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700 transition shrink-0"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">Incidentes</span>
              {incidentesAbertos > 0 && (
                <span className="w-4.5 h-4.5 rounded-full bg-rose-600 text-white text-[10px] flex items-center justify-center font-bold">
                  {incidentesAbertos}
                </span>
              )}
            </button>

            <button
              onClick={onOpenAuditoria}
              title="Trilha de Auditoria (Área Sensível)"
              className="p-1.5 sm:p-2 rounded-lg bg-[#161f30] hover:bg-slate-800 text-slate-300 border border-slate-700 transition shrink-0"
            >
              <FileText className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            </button>

            {/* Divisor */}
            <div className="h-5 w-[1px] bg-slate-800 mx-0.5 shrink-0" />

            {/* Estado de Acesso / Usuário */}
            {isAdmin ? (
              <div className="flex items-center gap-1.5 shrink-0">
                <div className="text-right hidden xl:block">
                  <div className="text-xs font-semibold text-slate-200 leading-tight">
                    {usuario.nome}
                  </div>
                  <div className="text-[9px] text-emerald-400 font-bold flex items-center justify-end gap-1">
                    <ShieldCheck className="w-2.5 h-2.5" />
                    ADMIN
                  </div>
                </div>
                <button
                  onClick={onLogout}
                  title="Bloquear Acesso / Voltar ao Modo Monitoramento"
                  className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-[#161f30] hover:bg-rose-950/50 text-slate-300 hover:text-rose-300 border border-slate-700 text-xs transition"
                >
                  <Unlock className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="hidden sm:inline">Bloquear</span>
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenLogin}
                title="Acesso com privilégios de Administrador"
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#161f30] hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700 transition shrink-0"
              >
                <Lock className="w-3.5 h-3.5 text-amber-400" />
                <span>Admin</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

