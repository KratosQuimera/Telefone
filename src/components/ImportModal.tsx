import React, { useState, useRef } from "react";
import { 
  X, 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  FileCode, 
  Download,
  Trash2
} from "lucide-react";

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (itens: any[]) => Promise<{ inseridos: number; atualizados: number }>;
}

export const ImportModal: React.FC<ImportModalProps> = ({
  isOpen,
  onClose,
  onImport,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsedItems, setParsedItems] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<{ inseridos: number; atualizados: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const processFile = (file: File) => {
    setError(null);
    setResultado(null);

    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Por favor selecione um arquivo válido com extensão .json");
      setSelectedFile(null);
      setParsedItems(null);
      return;
    }

    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const data = JSON.parse(text);
        let list: any[] = [];
        if (Array.isArray(data)) {
          list = data;
        } else if (data.ramais && Array.isArray(data.ramais)) {
          list = data.ramais;
        } else if (data.data && Array.isArray(data.data)) {
          list = data.data;
        } else {
          throw new Error("O JSON precisa conter um array direto ou uma propriedade 'ramais'.");
        }

        if (list.length === 0) {
          throw new Error("O arquivo JSON não contém nenhum ramal cadastrado.");
        }

        setParsedItems(list);
      } catch (err: any) {
        setError(`Erro ao ler arquivo JSON: ${err.message}`);
        setParsedItems(null);
      }
    };
    reader.onerror = () => {
      setError("Erro ao ler o arquivo do disco.");
      setParsedItems(null);
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const handleConfirmar = async () => {
    if (!parsedItems) return;
    setLoading(true);
    setError(null);
    try {
      const res = await onImport(parsedItems);
      setResultado(res);
    } catch (e: any) {
      setError(e.message || "Erro ao processar importação.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadModelo = () => {
    const modelo = [
      {
        numero: "2060",
        descricao: "Farmácia Central - Balcão 1",
        bloco: "Bloco Central",
        setor: "Farmácia",
        ip: "192.168.10.80",
        mac: "00:27:0D:B1:C2:E1",
        modelo: "Cisco CP-7841"
      },
      {
        numero: "2061",
        descricao: "CDI - Sala de Tomografia Computadorizada",
        bloco: "Bloco Central",
        setor: "CDI",
        ip: "192.168.10.81",
        mac: "00:27:0D:B1:C2:E2",
        modelo: "Cisco CP-8845"
      },
      {
        numero: "2070",
        descricao: "Emergência Pediátrica - Posto Enfermagem",
        bloco: "Pronto Socorro",
        setor: "Pediatria",
        ip: "192.168.10.82",
        mac: "00:27:0D:B1:C2:E3",
        modelo: "Cisco CP-7841"
      }
    ];

    const blob = new Blob([JSON.stringify(modelo, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "modelo_ramais_haoc.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const resetarSelecao = () => {
    setSelectedFile(null);
    setParsedItems(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="font-bold text-base">Importação de Ramais por Arquivo JSON</h3>
              <p className="text-[11px] text-slate-400">Carregamento seguro de planilhas e cadastros legados HAOC</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {resultado ? (
            <div className="p-6 text-center space-y-3">
              <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h4 className="text-lg font-bold text-slate-800">Arquivo Sincronizado com Sucesso!</h4>
              <p className="text-xs text-slate-600">
                Os registros do arquivo <strong>{selectedFile?.name}</strong> foram processados:
              </p>
              <div className="flex justify-center gap-4 py-2">
                <div className="bg-emerald-50 px-5 py-2.5 rounded-xl border border-emerald-200 text-center">
                  <span className="text-[11px] text-emerald-700 font-semibold uppercase">Novos Ramais</span>
                  <p className="text-2xl font-bold text-emerald-800">{resultado.inseridos}</p>
                </div>
                <div className="bg-sky-50 px-5 py-2.5 rounded-xl border border-sky-200 text-center">
                  <span className="text-[11px] text-sky-700 font-semibold uppercase">Atualizados</span>
                  <p className="text-2xl font-bold text-sky-800">{resultado.atualizados}</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="mt-4 px-6 py-2 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition"
              >
                Concluir e Ver Grade Atualizada
              </button>
            </div>
          ) : (
            <>
              {/* Dropzone de Arquivo */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                onChange={handleFileChange}
                className="hidden"
                id="json-file-input"
              />

              {!selectedFile ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                    isDragging
                      ? "border-emerald-500 bg-emerald-50/50 scale-[1.01]"
                      : "border-slate-300 hover:border-emerald-500 hover:bg-slate-50/80"
                  }`}
                >
                  <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3 border border-emerald-100">
                    <Upload className="w-7 h-7" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-800">
                    Arraste e solte o arquivo .JSON aqui
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">
                    ou <span className="text-emerald-600 font-semibold underline">clique para selecionar do computador</span>
                  </p>
                  <p className="text-[11px] text-slate-400 mt-2">
                    Suporta arquivos estruturados de ramais, nomes, IPs e MACs
                  </p>
                </div>
              ) : (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
                      <FileCode className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 text-xs">{selectedFile.name}</h4>
                      <p className="text-[11px] text-slate-500">
                        Tamanho: {(selectedFile.size / 1024).toFixed(1)} KB • {parsedItems ? `${parsedItems.length} ramais detectados` : "Validando..."}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={resetarSelecao}
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                    title="Remover arquivo"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Botão para Baixar Modelo */}
              <div className="flex items-center justify-between text-xs pt-1">
                <span className="text-slate-500">Precisa de um exemplo de arquivo compatível?</span>
                <button
                  type="button"
                  onClick={handleDownloadModelo}
                  className="flex items-center gap-1.5 text-emerald-600 hover:text-emerald-700 font-semibold"
                >
                  <Download className="w-3.5 h-3.5" />
                  Baixar Modelo .JSON
                </button>
              </div>

              {/* Erros */}
              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Pré-visualização dos Ramais */}
              {parsedItems && (
                <div className="border border-slate-200 rounded-xl overflow-hidden mt-3">
                  <div className="bg-slate-100 px-4 py-2 text-xs font-bold text-slate-700 flex justify-between items-center">
                    <span>Prévia de Importação: {parsedItems.length} registros prontos</span>
                    <span className="text-emerald-700 text-[11px] font-semibold">Estrutura Válida ✓</span>
                  </div>
                  <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs">
                    {parsedItems.slice(0, 10).map((it, idx) => (
                      <div key={idx} className="p-2.5 flex items-center justify-between hover:bg-slate-50">
                        <div>
                          <span className="font-bold text-slate-900 mr-2">Ramal {it.numero || it.ramal}</span>
                          <span className="text-slate-600">{it.descricao || it.nome}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-500 font-mono text-[11px]">{it.ip || "-"}</span>
                          <span className="text-slate-400 text-[11px]">{it.bloco || "Bloco Central"}</span>
                        </div>
                      </div>
                    ))}
                    {parsedItems.length > 10 && (
                      <div className="p-2 text-center text-slate-400 text-[11px] italic bg-slate-50/50">
                        + {parsedItems.length - 10} outros ramais presentes no arquivo...
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!resultado && (
          <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirmar}
              disabled={!parsedItems || loading}
              className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition shadow-xs ${
                parsedItems && !loading
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                  : "bg-slate-200 text-slate-400 cursor-not-allowed"
              }`}
            >
              <ArrowRight className="w-3.5 h-3.5" />
              {loading ? "Processando..." : parsedItems ? `Importar ${parsedItems.length} Ramais do Arquivo` : "Selecione um Arquivo .JSON"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
