import React, { useState, useRef } from "react";
import { 
  X, 
  Upload, 
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
  const [rawObject, setRawObject] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<{ inseridos: number; atualizados: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const normalizarDados = (data: any): any[] => {
    const listaNormalizada: any[] = [];

    // Formato Estruturado por Blocos: { "Bloco A": [ ... ], "Bloco B": [ ... ] }
    if (typeof data === "object" && !Array.isArray(data) && data !== null) {
      for (const [chaveBloco, valLista] of Object.entries(data)) {
        if (Array.isArray(valLista)) {
          for (const item of valLista) {
            if (!item || typeof item !== "object") continue;

            const modelo = item["Modelo"] || item["modelo"] || "Cisco 7841";
            const descricao = item["Descrição"] || item["Descricao"] || item["descricao"] || "";
            const ciscoId = item["I.P Cisco"] || item["MAC Cisco"] || item["mac_cisco"] || item["mac"] || "";
            const rawIp = item["I.P"] || item["ip"] || item["IP"] || "";

            const isNoneIp = !rawIp || String(rawIp).trim().toLowerCase() === "none" || String(rawIp).trim() === "-";
            const ip = isNoneIp ? "" : String(rawIp).trim();

            // Extrair número do ramal da descrição (fim, início ou qualquer número)
            let numero = item["numero"] || item["ramal"] || "";
            if (!numero && descricao) {
              const matchFim = descricao.match(/(?:-\s*|\b)(\d{3,5})\s*$/);
              const matchIni = descricao.match(/^\s*(\d{3,5})\b/);
              const matchAny = descricao.match(/\b(\d{3,5})\b/);
              if (matchFim) numero = matchFim[1];
              else if (matchIni) numero = matchIni[1];
              else if (matchAny) numero = matchAny[1];
            }

            // Normalizar MAC
            let mac = "";
            const ciscoStr = String(ciscoId).trim();
            if (ciscoStr.toUpperCase().startsWith("SEP") && ciscoStr.length === 15) {
              const hex = ciscoStr.slice(3).toUpperCase();
              mac = hex.match(/.{1,2}/g)?.join(":") || hex;
            } else if (ciscoStr.toUpperCase().startsWith("CSF")) {
              mac = ciscoStr.toUpperCase();
            } else if (ciscoStr) {
              const clean = ciscoStr.replace(/[^0-9A-Fa-f]/g, "").toUpperCase();
              if (clean.length === 12) {
                mac = clean.match(/.{1,2}/g)?.join(":") || clean;
              } else {
                mac = ciscoStr;
              }
            }

            // Extrair setor
            let setor = item["Setor"] || item["setor"] || "";
            if (!setor && descricao) {
              const partes = descricao.split(" - ").map((s: string) => s.trim()).filter(Boolean);
              if (partes.length >= 3) {
                const penultima = partes[partes.length - 2];
                if (/^\d+$/.test(penultima) && partes.length >= 4) {
                  setor = partes[partes.length - 3];
                } else {
                  setor = penultima;
                }
              } else if (partes.length === 2) {
                setor = /^\d+$/.test(partes[1]) ? partes[0] : partes[1];
              }
            }
            if (!setor) setor = "Geral";

            listaNormalizada.push({
              numero: String(numero || "").trim() || "S/N",
              descricao: descricao || `Ramal ${numero}`,
              bloco: item["Bloco"] || item["bloco"] || chaveBloco,
              setor,
              ip,
              mac_cisco: mac || ciscoId || "00:27:0D:00:00:00",
              cisco_id: ciscoId,
              modelo,
              status: ip ? "ONLINE" : "OFFLINE",
            });
          }
        }
      }
    } else if (Array.isArray(data)) {
      // Compatibilidade com lista plana
      for (const item of data) {
        if (!item || typeof item !== "object") continue;
        const modelo = item["Modelo"] || item["modelo"] || "Cisco 7841";
        const descricao = item["Descrição"] || item["Descricao"] || item["descricao"] || "";
        const ciscoId = item["I.P Cisco"] || item["MAC Cisco"] || item["mac_cisco"] || item["mac"] || "";
        const rawIp = item["I.P"] || item["ip"] || item["IP"] || "";
        const isNoneIp = !rawIp || String(rawIp).trim().toLowerCase() === "none" || String(rawIp).trim() === "-";
        const ip = isNoneIp ? "" : String(rawIp).trim();

        let numero = item["numero"] || item["ramal"] || "";
        if (!numero && descricao) {
          const matchFim = descricao.match(/(?:-\s*|\b)(\d{3,5})\s*$/);
          const matchIni = descricao.match(/^\s*(\d{3,5})\b/);
          if (matchFim) numero = matchFim[1];
          else if (matchIni) numero = matchIni[1];
        }

        listaNormalizada.push({
          numero: String(numero || "").trim() || "S/N",
          descricao: descricao || `Ramal ${numero}`,
          bloco: item["Bloco"] || item["bloco"] || "Bloco Central",
          setor: item["Setor"] || item["setor"] || "Geral",
          ip,
          mac_cisco: ciscoId || "00:27:0D:00:00:00",
          cisco_id: ciscoId,
          modelo,
          status: ip ? "ONLINE" : "OFFLINE",
        });
      }
    }

    return listaNormalizada;
  };

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
        setRawObject(data);

        const list = normalizarDados(data);
        if (list.length === 0) {
          throw new Error("Nenhum ramal válido foi encontrado no arquivo JSON. Verifique as chaves de bloco.");
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
      // Enviar rawObject se existir para o backend preservar estrutura oficial por blocos
      const payloadParaEnvio = rawObject || parsedItems;
      const res = await onImport(payloadParaEnvio);
      setResultado(res);
    } catch (e: any) {
      setError(e.message || "Erro ao processar importação.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadModelo = () => {
    const modeloOficial = {
      "Bloco A": [
        {
          "Modelo": "Cisco Unified Client Services Framework",
          "I.P Cisco": "CSF18982",
          "Descrição": "JABBER - Recp_Bl.A - Ouvidoria - 6452",
          "I.P": "None"
        },
        {
          "Modelo": "Cisco 7841",
          "I.P Cisco": "SEP2C86D276454B",
          "Descrição": "Matriz - 1A Bl.A - Juridico - 0351",
          "I.P": "10.192.58.24"
        }
      ],
      "Bloco B": [
        {
          "Modelo": "Cisco 7841",
          "I.P Cisco": "SEP2C86D2764624",
          "Descrição": "Matriz - 10A_Bl.B - 10B Quarto 1000 - 1000",
          "I.P": "10.193.28.25"
        },
        {
          "Modelo": "Cisco 7841",
          "I.P Cisco": "SEP2C3ECF86C880",
          "Descrição": "Matriz - 10A_Bl.B - 10B Quarto 1001 - 1001",
          "I.P": "10.193.28.130"
        }
      ],
      "Bloco E": [
        {
          "Modelo": "Cisco 7841",
          "I.P Cisco": "SEP2C3ECF87F9C5",
          "Descrição": "Matriz - 10A_Bl.E - 10E Quarto 1016 - 1016",
          "I.P": "10.195.28.91"
        },
        {
          "Modelo": "Cisco 7841",
          "I.P Cisco": "SEP2C3ECF86C4AB",
          "Descrição": "Matriz - 10A_Bl.E - 10E Quarto 1017 - 1017",
          "I.P": "10.195.28.165"
        }
      ]
    };

    const blob = new Blob([JSON.stringify(modeloOficial, null, 2)], { type: "application/json" });
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
    setRawObject(null);
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
              <p className="text-[11px] text-slate-400">Modelo Oficial Cisco estruturado por Blocos</p>
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
                Os registros do arquivo <strong>{selectedFile?.name}</strong> foram integrados com êxito:
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
                Concluir e Ver Painel Atualizado
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
                    Formato por Blocos (ex: "Bloco A", "Bloco B") com Modelo, I.P Cisco, Descrição e I.P
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
                        Tamanho: {(selectedFile.size / 1024).toFixed(1)} KB • {parsedItems ? `${parsedItems.length} ramais mapeados` : "Validando..."}
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
                <span className="text-slate-500">Formato oficial por blocos (Bloco A, B, E):</span>
                <button
                  type="button"
                  onClick={handleDownloadModelo}
                  className="flex items-center gap-1.5 text-emerald-600 hover:text-emerald-700 font-semibold"
                >
                  <Download className="w-3.5 h-3.5" />
                  Baixar Modelo Oficial .JSON
                </button>
              </div>

              {/* Erros */}
              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Pré-visualização dos Ramais Mapeados */}
              {parsedItems && (
                <div className="border border-slate-200 rounded-xl overflow-hidden mt-3">
                  <div className="bg-slate-100 px-4 py-2 text-xs font-bold text-slate-700 flex justify-between items-center">
                    <span>Prévia de Importação: {parsedItems.length} ramais estruturados</span>
                    <span className="text-emerald-700 text-[11px] font-semibold">Estrutura Reconhecida ✓</span>
                  </div>
                  <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs">
                    {parsedItems.map((it, idx) => (
                      <div key={idx} className="p-2.5 flex items-center justify-between hover:bg-slate-50">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">Ramal {it.numero}</span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-200 text-slate-700">{it.bloco}</span>
                            {it.status === "ONLINE" ? (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-700">ONLINE</span>
                            ) : (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-100 text-rose-700">OFFLINE (None)</span>
                            )}
                          </div>
                          <p className="text-slate-600 text-[11px] truncate max-w-sm">{it.descricao}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-slate-700 font-mono text-[11px] font-medium">{it.ip || "I.P: None"}</p>
                          <p className="text-slate-400 font-mono text-[10px]">{it.cisco_id || it.mac_cisco}</p>
                        </div>
                      </div>
                    ))}
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
