import express from "express";
import path from "path";
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
    const { ramal, usuario_nome } = req.body;
    if (!ramal || !ramal.numero || !ramal.descricao) {
      return res.status(400).json({ erro: "Número e descrição são obrigatórios." });
    }
    const salvo = store.salvarRamal(ramal, usuario_nome || "Wagner");
    res.json(salvo);
  });

  // Desativar Ramal
  app.delete("/api/ramais/:id", (req, res) => {
    const id = parseInt(req.params.id, 10);
    const usuario_nome = (req.query.usuario_nome as string) || "Wagner";
    const ok = store.desativarRamal(id, usuario_nome);
    if (ok) {
      res.json({ sucesso: true });
    } else {
      res.status(404).json({ erro: "Ramal não encontrado." });
    }
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
    const resultado = store.pingAll();
    res.json(resultado);
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

  // Importação JSON Legado
  app.post("/api/importar", (req, res) => {
    const { itens, usuario_nome } = req.body;
    if (!Array.isArray(itens)) {
      return res.status(400).json({ erro: "Estrutura JSON inválida: lista de ramais esperada." });
    }
    const resultado = store.importarJsonLegado(itens, usuario_nome || "Wagner");
    res.json(resultado);
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
