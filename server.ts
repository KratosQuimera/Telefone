import express from "express";
import path from "path";
import fs from "fs";
import { createServer as createViteServer } from "vite";
import { store } from "./server/store";

const PORT = 3000;

async function startServer() {
  const app = express();

  app.use(express.json({ limit: "10mb" }));
  app.use(express.urlencoded({ extended: true }));

  // --- API ROUTES ---

  // Health check
  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // Autenticação
  app.post("/api/auth/login", (req, res) => {
    const { login, senha } = req.body;
    if (!login || !senha) {
      return res.status(400).json({ erro: "Usuário e senha são obrigatórios." });
    }
    const usuario = store.autenticar(login, senha);
    if (!usuario) {
      return res.status(401).json({ erro: "Credenciais inválidas ou usuário inativo." });
    }
    res.json({
      sucesso: true,
      usuario,
    });
  });

  // Estatísticas Gerais e SLA
  app.get("/api/stats", (_req, res) => {
    res.json(store.getStats());
  });

  // Listagem de Ramais
  app.get("/api/ramais", (req, res) => {
    const { bloco, status, search } = req.query as { bloco?: string; status?: string; search?: string };
    const ramais = store.getRamais({ bloco, status, search });
    res.json(ramais);
  });

  // Salvar ou Atualizar Ramal
  app.post("/api/ramais", (req, res) => {
    let ramal = req.body?.ramal || req.body;
    const usuario_nome = req.body?.usuario_nome || "Wagner";
    if (!ramal || typeof ramal !== "object") {
      return res.status(400).json({ erro: "Dados do ramal inválidos." });
    }
    if (!ramal.numero && ramal.descricao) {
      const match = String(ramal.descricao).match(/\b(\d{3,5})\b/);
      if (match) {
        ramal.numero = match[1];
      } else if (ramal.id) {
        ramal.numero = String(ramal.id);
      }
    }
    if (!ramal.descricao) {
      return res.status(400).json({ erro: "Descrição do ramal é obrigatória." });
    }
    if (!ramal.numero) {
      ramal.numero = String(ramal.id || "1000");
    }
    const salvo = store.salvarRamal(ramal, usuario_nome);
    const ramaisAtualizados = store.getRamais();
    const statsAtualizados = store.getStats();

    res.json({
      ...salvo,
      ramal: salvo,
      ramais: ramaisAtualizados,
      stats: statsAtualizados,
      mensagem: `Ramal ${salvo.numero} salvo com sucesso. Ping testado: status ${salvo.status} (${salvo.latencia_ms ? salvo.latencia_ms + "ms" : "sem resposta"}).`,
    });
  });

  // Atualizar Ramal via PUT /api/ramais/:id
  app.put("/api/ramais/:id", (req, res) => {
    let ramal = req.body?.ramal || req.body || {};
    const idParam = req.params.id;
    const numId = parseInt(idParam, 10);
    ramal.id = isNaN(numId) ? idParam : numId;
    const usuario_nome = req.body?.usuario_nome || "Wagner";

    if (!ramal.numero && ramal.descricao) {
      const match = String(ramal.descricao).match(/\b(\d{3,5})\b/);
      if (match) {
        ramal.numero = match[1];
      } else {
        ramal.numero = String(ramal.id);
      }
    }
    const salvo = store.salvarRamal(ramal, usuario_nome);
    const ramaisAtualizados = store.getRamais();
    const statsAtualizados = store.getStats();

    res.json({
      ...salvo,
      ramal: salvo,
      ramais: ramaisAtualizados,
      stats: statsAtualizados,
      mensagem: `Ramal ${salvo.numero} atualizado com sucesso no JSON.`,
    });
  });

  // Excluir Ramal e atualizar arquivos JSON
  app.delete("/api/ramais/:id", (req, res) => {
    const rawId = req.params.id;
    const numId = parseInt(rawId, 10);
    const idToUse = isNaN(numId) ? rawId : numId;
    const usuario_nome = (req.query.usuario_nome as string) || (req.body && req.body.usuario_nome) || "Wagner";
    const resultado = store.excluirRamal(idToUse, usuario_nome, req.body);

    const ramaisAtualizados = store.getRamais();
    const statsAtualizados = store.getStats();

    res.json({
      sucesso: true,
      mensagem: `Ramal ${resultado.ramal?.numero || rawId} excluído com sucesso e arquivos JSON sincronizados.`,
      ramais: ramaisAtualizados,
      stats: statsAtualizados,
      arquivosModificados: resultado.arquivosModificados || [],
    });
  });

  // Ping em Lotes (Dividido para não sobrecarregar CPU e memória)
  app.post("/api/ramais/ping-lote", (req, res) => {
    const { ids } = req.body;
    if (!Array.isArray(ids) || ids.length === 0) {
      return res.status(400).json({ erro: "Lista de IDs ('ids') é obrigatória para ping em lote." });
    }
    const resultados = store.pingLote(ids);
    res.json({
      sucesso: true,
      processados: resultados.length,
      resultados,
    });
  });

  // Ping Individual
  app.post("/api/ramais/:id/ping", (req, res) => {
    const id = parseInt(req.params.id, 10);
    try {
      const resultado = store.pingRamal(id);
      res.json(resultado);
    } catch (err: any) {
      res.status(404).json({ erro: err.message });
    }
  });

  // Ping Geral / Varredura Completa
  app.post("/api/ping-all", (_req, res) => {
    try {
      const resultado = store.pingAll();
      const ramaisAtualizados = store.getRamais();
      const statsAtualizados = store.getStats();
      res.json({
        ...resultado,
        sucesso: true,
        ramais: ramaisAtualizados,
        stats: statsAtualizados,
        mensagem: `Varredura geral concluída: ${resultado.total} ramais verificados (${resultado.online} online, ${resultado.offline} offline).`,
      });
    } catch (err: any) {
      console.error("[Server] Erro na rota /api/ping-all:", err);
      res.status(500).json({ erro: err?.message || "Falha na verificação geral." });
    }
  });

  // Incidentes
  app.get("/api/incidentes", (_req, res) => {
    res.json(store.getIncidentes());
  });

  // Resolver Incidente
  app.post("/api/incidentes/:id/resolver", (req, res) => {
    const id = parseInt(req.params.id, 10);
    const usuario_nome = req.body.usuario_nome || "Wagner";
    const ok = store.resolverIncidente(id, usuario_nome);
    if (ok) {
      res.json({ sucesso: true });
    } else {
      res.status(404).json({ erro: "Incidente não encontrado." });
    }
  });

  // Usuários
  app.get("/api/usuarios", (_req, res) => {
    res.json(store.getUsuarios());
  });

  // Auditoria
  app.get("/api/auditoria", (_req, res) => {
    res.json(store.getAuditoria());
  });

  // Importação e Exportação JSON no Modelo Oficial por Blocos
  app.post("/api/importar", (req, res) => {
    const payload = req.body;
    const usuarioNome = payload.usuario_nome || "Wagner";
    const conteudo = payload.itens || payload.dados || payload.data || payload;

    if (!conteudo || (typeof conteudo !== "object" && !Array.isArray(conteudo))) {
      return res.status(400).json({ erro: "Estrutura JSON inválida: objeto com blocos ou lista esperada." });
    }

    try {
      const resultado = store.importarJsonLegado(conteudo, usuarioNome);
      res.json(resultado);
    } catch (err: any) {
      res.status(500).json({ erro: err.message || "Falha ao processar JSON." });
    }
  });

  // Sincronização Automática com Pasta de Rede
  app.get("/api/rede/config", (_req, res) => {
    res.json(store.getNetworkConfig());
  });

  app.post("/api/rede/config", (req, res) => {
    const { caminho, auto_sync } = req.body;
    const cfg = store.setNetworkConfig(caminho || "", auto_sync !== false);
    res.json(cfg);
  });

  app.post("/api/rede/sincronizar", (req, res) => {
    const { caminho } = req.body || {};
    const resultado = store.sincronizarCaminhoRede(caminho);
    res.json(resultado);
  });

  // Exportação em formato JSON oficial estruturado por Blocos
  app.get("/api/exportar-json", (_req, res) => {
    res.setHeader("Content-Disposition", "attachment; filename=ramais_haoc.json");
    res.setHeader("Content-Type", "application/json");
    res.json(store.exportarJsonModelo());
  });

  // Download do arquivo de modelo padrão
  app.get("/api/modelo-json", (_req, res) => {
    const modeloPath = path.join(process.cwd(), "data", "modelo_ramais_haoc.json");
    if (fs.existsSync(modeloPath)) {
      res.setHeader("Content-Disposition", "attachment; filename=modelo_ramais_haoc.json");
      res.setHeader("Content-Type", "application/json");
      return res.sendFile(modeloPath);
    }
    res.json(store.exportarJsonModelo());
  });

  // Download do arquivo .bat para criar executável Windows
  app.get("/api/download-bat", (_req, res) => {
    const batPath = path.join(process.cwd(), "criar_executavel_desktop.bat");
    if (fs.existsSync(batPath)) {
      res.setHeader("Content-Disposition", "attachment; filename=criar_executavel_desktop.bat");
      res.setHeader("Content-Type", "application/x-bat");
      return res.sendFile(batPath);
    }
    res.status(404).send("Arquivo .bat não encontrado");
  });

  // --- VITE MIDDLEWARE SETUP ---
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`[HAOC VoIP Gateway] Servidor rodando em http://0.0.0.0:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error("[HAOC VoIP Gateway Fatal]", err);
});
