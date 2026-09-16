import React, { useState, useEffect } from "react";
import { X, Save, Phone, MapPin, Tag, Globe, Cpu, AlertCircle } from "lucide-react";
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
      setNumero(ramalEditar.numero);
      setDescricao(ramalEditar.descricao);
      setBloco(ramalEditar.bloco);
      setSetor(ramalEditar.setor);
      setIp(ramalEditar.ip);
      setMac(ramalEditar.mac_cisco);
      setModelo(ramalEditar.modelo);
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
    if (!numero.trim() || !descricao.trim()) {
      setErro("Por favor preencha o número do ramal e a descrição.");
      return;
    }

    setLoading(true);
    setErro(null);

    try {
      await onSave({
        id: ramalEditar ? ramalEditar.id : undefined,
        numero: numero.trim(),
        descricao: descricao.trim(),
        bloco,
        setor: setor.trim() || "Geral",
        ip: ip.trim(),
        mac_cisco: mac.trim(),
        modelo: modelo.trim(),
      });
      onClose();
    } catch (err: any) {
      setErro(err.message || "Erro ao salvar ramal.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-base">
              {ramalEditar ? `Editar Ramal ${ramalEditar.numero}` : "Novo Ramal VoIP HAOC"}
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {erro && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{erro}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Número do Ramal *
              </label>
              <input
                type="text"
                required
                placeholder="Ex: 2045"
                value={numero}
                onChange={(e) => setNumero(e.target.value)}
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-bold"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Modelo do Aparelho
              </label>
              <select
                value={modelo}
                onChange={(e) => setModelo(e.target.value)}
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Descrição / Identificação Hospitalar *
            </label>
            <input
              type="text"
              required
              placeholder="Ex: Posto de Coleta - Laboratório Central"
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Bloco Hospitalar
              </label>
              <select
                value={bloco}
                onChange={(e) => setBloco(e.target.value)}
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              >
                {BLOCOS_PADRAO.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Setor / Especialidade
              </label>
              <input
                type="text"
                placeholder="Ex: Farmácia Satélite"
                value={setor}
                onChange={(e) => setSetor(e.target.value)}
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Endereço IPv4
              </label>
              <input
                type="text"
                placeholder="Ex: 192.168.10.45"
                value={ip}
                onChange={(e) => setIp(e.target.value)}
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                MAC Address Cisco
              </label>
              <input
                type="text"
                placeholder="00:27:0D:XX:XX:XX"
                value={mac}
                onChange={(e) => setMac(e.target.value)}
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono uppercase"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition shadow-xs"
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
