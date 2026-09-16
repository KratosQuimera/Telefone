import React, { useState } from "react";
import { X, Lock, User, ShieldAlert, ArrowRight, ShieldCheck, KeyRound } from "lucide-react";
import { Usuario } from "../types";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (usuario: Usuario) => void;
  motivoAcesso?: string | null;
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  onLoginSuccess,
  motivoAcesso,
}) => {
  const [login, setLogin] = useState("Wagner");
  const [senha, setSenha] = useState("SenhaTel@Haoc");
  const [erro, setErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErro(null);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login, senha }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.erro || "Credenciais inválidas.");
      }

      onLoginSuccess(data.usuario);
      onClose();
    } catch (err: any) {
      setErro(err.message || "Falha ao validar credenciais.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickMaster = () => {
    setLogin("Wagner");
    setSenha("SenhaTel@Haoc");
    setErro(null);
  };

  return (
    <div className="fixed inset-0 bg-slate-900/65 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-600 flex items-center justify-center shadow-xs">
              <KeyRound className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-base">Acesso à Área Sensível</h3>
              <p className="text-[11px] text-slate-400">Autenticação com privilégios de administrador</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Motivo de Acesso Sensível */}
        {motivoAcesso && (
          <div className="bg-amber-50 border-b border-amber-200/80 px-6 py-2.5 flex items-center gap-2 text-xs text-amber-900">
            <Lock className="w-4 h-4 text-amber-700 shrink-0" />
            <span>
              Ação solicitada: <strong>{motivoAcesso}</strong>
            </span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-slate-500 leading-relaxed">
            O monitoramento básico é de livre visualização. Para alterar configurações, cadastros ou registros críticos, confirme suas credenciais:
          </p>

          {erro && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{erro}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Usuário / Login
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                className="w-full text-sm pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Senha de Acesso
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                className="w-full text-sm pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>

          {/* Atalho Master Wagner */}
          <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-xl flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
                <p className="text-xs font-bold text-emerald-950">Acesso Master Wagner</p>
              </div>
              <p className="text-[11px] text-emerald-700 font-mono mt-0.5">Wagner • SenhaTel@Haoc</p>
            </div>
            <button
              type="button"
              onClick={handleQuickMaster}
              className="text-xs font-semibold text-emerald-700 bg-white px-2.5 py-1 rounded-md border border-emerald-300 hover:bg-emerald-100 transition shadow-2xs"
            >
              Preencher
            </button>
          </div>

          {/* Botões */}
          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Voltar ao Monitor
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition shadow-xs"
            >
              <ArrowRight className="w-3.5 h-3.5" />
              {loading ? "Validando..." : "Confirmar e Acessar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
