import React, { useState } from "react";
import { X, Package, Terminal, Check, Copy, ExternalLink, ShieldCheck } from "lucide-react";

interface ExeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ExeModal: React.FC<ExeModalProps> = ({ isOpen, onClose }) => {
  const [copied, setCopied] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  const scriptBat = `build_windows.bat`;
  const scriptPython = `python build_exe.py`;

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-indigo-950 text-white px-6 py-4 flex items-center justify-between border-b border-indigo-900">
          <div className="flex items-center gap-2">
            <Package className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-base">
              Gerar Executável Desktop (.EXE) para Windows 10/11
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-700">
          <div className="p-4 bg-indigo-50/60 border border-indigo-200 rounded-xl">
            <div className="flex items-start gap-2.5">
              <ShieldCheck className="w-5 h-5 text-indigo-700 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-indigo-950 text-sm">Distribuição Standalone Hospitalar</h4>
                <p className="text-indigo-900/80 mt-1 leading-relaxed">
                  O projeto já conta com o arquivo de especificação do PyInstaller (<strong>haoc_voip_desktop.spec</strong>) 
                  e os scripts automatizados prontos. Basta executar o comando abaixo na máquina Windows para gerar o 
                  <strong> HAOC_VoIP_Monitor.exe</strong> com interface nativa PyQt6 e o usuário Master <strong>Wagner</strong>.
                </p>
              </div>
            </div>
          </div>

          {/* Método 1 */}
          <div className="space-y-2">
            <h4 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] flex items-center justify-center font-bold">1</span>
              Método 1: Duplo-Clique Automático (1 Clique no Windows)
            </h4>
            <p className="text-slate-500">
              Na pasta raiz do projeto exportado ou clonado, basta dar duplo-clique no arquivo:
            </p>
            <div className="flex items-center justify-between bg-slate-900 text-emerald-400 font-mono p-3 rounded-xl">
              <span>{scriptBat}</span>
              <button
                onClick={() => copyToClipboard(scriptBat, "bat")}
                className="text-slate-400 hover:text-white p-1"
                title="Copiar nome do arquivo"
              >
                {copied === "bat" ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Método 2 */}
          <div className="space-y-2">
            <h4 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] flex items-center justify-center font-bold">2</span>
              Método 2: Linha de Comando (PowerShell / Prompt)
            </h4>
            <div className="flex items-center justify-between bg-slate-900 text-emerald-400 font-mono p-3 rounded-xl">
              <span>{scriptPython}</span>
              <button
                onClick={() => copyToClipboard(scriptPython, "py")}
                className="text-slate-400 hover:text-white p-1"
                title="Copiar comando"
              >
                {copied === "py" ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Resultado */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1.5">
            <p className="font-bold text-slate-900">Arquivo gerado final:</p>
            <p className="font-mono text-indigo-700 font-semibold bg-white p-2 rounded border border-slate-200">
              dist/HAOC_VoIP_Monitor.exe
            </p>
            <p className="text-slate-500 text-[11px]">
              ✓ Não requer Python nas estações dos analistas/telefonistas.<br />
              ✓ Sem janela preta de console (modo janela limpa).<br />
              ✓ Banco SQLite em modo WAL com integridade e backups automáticos.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white rounded-lg transition"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};
