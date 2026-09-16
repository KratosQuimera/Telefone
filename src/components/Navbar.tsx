import React from "react";
import { 
  PhoneCall, 
  Plus, 
  Upload, 
  AlertTriangle, 
  Package, 
  LogOut, 
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
  onOpenIncidentes: () => void;
  onOpenAuditoria: () => void;
  onOpenExe: () => void;
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
  onOpenIncidentes,
  onOpenAuditoria,
  onOpenExe,
  onPingAll,
  isScanning,
  incidentesAbertos,
}) => {
  const isAdmin = usuario?.perfil === "ADMINISTRADOR";

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center shadow-md">
              <PhoneCall className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight">HAOC VoIP</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-medium">
                  ENTERPRISE
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Hospital Augusto de Oliveira Camargo • Centro de Telefonia IP
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Ping Geral (Livre) */}
            <button
              onClick={onPingAll}
              disabled={isScanning}
              title="Disparar teste de conectividade em todos os ramais"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isScanning 
                  ? "bg-slate-800 text-slate-400 cursor-not-allowed" 
                  : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-xs"
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? "animate-spin" : ""}`} />
              <span className="hidden md:inline">{isScanning ? "Varrendo..." : "Verificar Todos"}</span>
            </button>

            {/* Ações Administrativas / Sensíveis */}
            <button
              onClick={onOpenNovoRamal}
              title="Cadastrar novo ramal (Área Sensível)"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden md:inline">Novo Ramal</span>
            </button>

            <button
              onClick={onOpenImport}
              title="Carregar arquivo .JSON (Área Sensível)"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
            >
              <Upload className="w-3.5 h-3.5 text-sky-400" />
              <span className="hidden md:inline">Importar JSON</span>
            </button>

            <button
              onClick={onOpenIncidentes}
              className="relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden md:inline">Incidentes</span>
              {incidentesAbertos > 0 && (
                <span className="w-5 h-5 rounded-full bg-rose-600 text-white text-[10px] flex items-center justify-center font-bold">
                  {incidentesAbertos}
                </span>
              )}
            </button>

            <button
              onClick={onOpenAuditoria}
              title="Trilha de Auditoria (Área Sensível)"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              <FileText className="w-4 h-4" />
            </button>

            <button
              onClick={onOpenExe}
              title="Gerar Executável Desktop (.exe)"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-900/60 hover:bg-indigo-900 text-indigo-200 text-xs font-semibold border border-indigo-700/60 transition"
            >
              <Package className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden lg:inline">Gerar .EXE</span>
            </button>

            {/* Divisor */}
            <div className="h-6 w-[1px] bg-slate-800 mx-1" />

            {/* Estado de Acesso / Usuário */}
            {isAdmin ? (
              <div className="flex items-center gap-2">
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-semibold text-slate-200 leading-tight">
                    {usuario.nome}
                  </div>
                  <div className="text-[10px] text-emerald-400 font-medium flex items-center justify-end gap-1">
                    <ShieldCheck className="w-2.5 h-2.5" />
                    ADMINISTRADOR
                  </div>
                </div>
                <button
                  onClick={onLogout}
                  title="Bloquear Acesso / Voltar ao Modo Monitoramento"
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-900/40 text-slate-400 hover:text-rose-300 border border-slate-700 text-xs transition"
                >
                  <Unlock className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="hidden md:inline">Bloquear</span>
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenLogin}
                title="Acesso com privilégios de Administrador"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
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
