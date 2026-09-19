import React, { useState, useEffect } from "react";
import { X, Save, Phone, AlertCircle, Cpu, MapPin, Tag } from "lucide-react";
import { Ramal } from "../types";

interface RamalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (ramalData: Partial<Ramal>) => Promise<void>;
  ramalEditar: Ramal | null;
}

const BLOCOS_PADRAO = [
  "Bloco Central",
  "Pronto Socorro",
  "UTI Geral",
  "Centro Cirúrgico",
  "Maternidade",
  "Ambulatório",
  "Administrativo",
];

export const RamalModal: React.FC<RamalModalProps> = ({
  isOpen,
  onClose,
  onSave,
  ramalEditar,
}) => {
  const [numero, setNumero] = useState("");
  const [descricao, setDescricao] = useState("");
  const [bloco, setBloco] = useState("Bloco Central");
  const [setor, setSetor] = useState("");
  const [ip, setIp] = useState("192.168.10.");
  const [mac, setMac] = useState("00:27:0D:");
  const [modelo, setModelo] = useState("Cisco CP-7841");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (ramalEditar) {
      setNumero(String(ramalEditar.numero || ""));
      setDescricao(String(ramalEditar.descricao || ""));
      setBloco(String(ramalEditar.bloco || "Bloco Central"));
      setSetor(String(ramalEditar.setor || ""));
      setIp(String(ramalEditar.ip || ""));
      setMac(String(ramalEditar.mac_cisco || ""));
      setModelo(String(ramalEditar.modelo || "Cisco CP-7841"));
    } else {
      setNumero("");
      setDescricao("");
      setBloco("Bloco Central");
      setSetor("");
      setIp("192.168.10.100");
      setMac("00:27:0D:A1:B2:D0");
      setModelo("Cisco CP-7841");
    }
    setErro(null);
  }, [ramalEditar, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    const numLimpo = String(numero || "").trim();
    const descLimpa = String(descricao || "").trim();

    if (!numLimpo || !descLimpa) {
      setErro("Por favor preencha o número do ramal e a descrição.");
      return;
    }

    setLoading(true);
    setErro(null);

    try {
      await onSave({
        id: ramalEditar?.id,
        numero: numLimpo,
        descricao: descLimpa,
        bloco: String(bloco || "Bloco Central"),
        setor: String(setor || "").trim() || "Geral",
        ip: String(ip || "").trim(),
        mac_cisco: String(mac || "").trim(),
        modelo: String(modelo || "Cisco CP-7841").trim(),
      });
      onClose();
    } catch (err: any) {
      setErro(err?.message || "Erro ao salvar ramal.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
      <div 
        className="bg-[#111827] rounded-2xl max-w-lg w-full shadow-2xl border border-slate-700/80 overflow-hidden text-slate-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-[#0b0f19] border-b border-slate-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-950 border border-emerald-700 flex items-center justify-center text-emerald-400">
              <Phone className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">
                {ramalEditar ? `Editar Ramal ${ramalEditar.numero}` : "Novo Ramal VoIP HAOC"}
              </h3>
              <p className="text-[11px] text-slate-400">Hospital Alemão Osvaldo Cruz</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            disabled={loading}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {erro && (
            <div className="p-3 bg-rose-950/80 border border-rose-700 rounded-lg text-rose-200 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{erro}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Número do Ramal *
              </label>
              <input
                type="text"
                required
                placeholder="Ex: 2045"
                value={numero}
                onChange={(e) => setNumero(e.target.value)}
                className="w-full text-sm px-3 py-2 bg-[#0f172a] border border-slate-700 rounded-lg text-white font-bold focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Modelo do Aparelho
              </label>
              <select
                value={modelo}
                onChange={(e) => setModelo(e.target.value)}
                className="w-full text-sm px-3 py-2 bg-[#0f172a] border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              >
                <option value="Cisco CP-7841">Cisco CP-7841</option>
                <option value="Cisco CP-7821">Cisco CP-7821</option>
                <option value="Cisco CP-8841">Cisco CP-8841</option>
                <option value="Cisco CP-8845">Cisco CP-8845</option>
                <option value="Cisco CP-8861">Cisco CP-8861</option>
                <option value="Cisco CP-3905">Cisco CP-3905</option>
                <option value="Cisco ATA-191">Cisco ATA-191</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Descrição / Identificação Hospitalar *
            </label>
            <input
              type="text"
              required
              placeholder="Ex: Posto de Coleta - Laboratório Central"
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              className="w-full text-sm px-3 py-2 bg-[#0f172a] border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Bloco Hospitalar
              </label>
              <select
                value={bloco}
                onChange={(e) => setBloco(e.target.value)}
                className="w-full text-sm px-3 py-2 bg-[#0f172a] border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              >
                {BLOCOS_PADRAO.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Setor / Especialidade
              </label>
              <input
                type="text"
                placeholder="Ex: Farmácia Satélite"
                value={setor}
                onChange={(e) => setSetor(e.target.value)}
                className="w-full text-sm px-3 py-2 bg-[#0f172a] border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Endereço IPv4
              </label>
              <input
                type="text"
                placeholder="Ex: 192.168.10.45"
                value={ip}
                onChange={(e) => setIp(e.target.value)}
                className="w-full text-sm px-3 py-2 bg-[#0f172a] border border-slate-700 rounded-lg text-sky-400 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                MAC Address Cisco
              </label>
              <input
                type="text"
                placeholder="00:27:0D:XX:XX:XX"
                value={mac}
                onChange={(e) => setMac(e.target.value)}
                className="w-full text-sm px-3 py-2 bg-[#0f172a] border border-slate-700 rounded-lg text-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono uppercase"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg transition shadow-md shadow-emerald-950/50"
            >
              <Save className="w-3.5 h-3.5" />
              {loading ? "Salvando..." : ramalEditar ? "Atualizar Ramal" : "Salvar Ramal"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
