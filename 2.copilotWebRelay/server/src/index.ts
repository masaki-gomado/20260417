import express from "express";
import { createServer } from "node:http";
import { WebSocketServer, WebSocket } from "ws";
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const PORT = 3001;

async function main() {
  const client = new CopilotClient();
  await client.start();
  console.log("[server] CopilotClient started");

  const app = express();

  // CORS for local development
  app.use((_req, res, next) => {
    res.setHeader("Access-Control-Allow-Origin", "http://localhost:5173");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    next();
  });

  app.get("/health", (_req, res) => {
    res.json({ status: "ok" });
  });

  const server = createServer(app);
  const wss = new WebSocketServer({ server, path: "/ws" });

  wss.on("connection", async (ws: WebSocket) => {
    console.log("[ws] client connected");

    let session: Awaited<ReturnType<typeof client.createSession>> | null = null;
    let sessionReady = false;
    const pendingMessages: string[] = [];

    // Register message handler immediately to avoid losing messages
    // that arrive while the session is being created
    ws.on("message", async (raw: Buffer) => {
      try {
        const data = JSON.parse(raw.toString()) as { type: string; content: string };

        if (data.type === "message" && data.content) {
          if (sessionReady && session) {
            console.log("[ws] user message received");
            await session.send({ prompt: data.content });
          } else {
            console.log("[ws] buffering message (session not ready)");
            pendingMessages.push(data.content);
          }
        }
      } catch (err) {
        console.error("[ws] error handling message:", err);
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "error", message: "Failed to process message" }));
        }
      }
    });

    ws.on("close", async () => {
      console.log("[ws] client disconnected");
      if (session) {
        try {
          await session.disconnect();
          console.log("[ws] copilot session disconnected");
        } catch (err) {
          console.error("[ws] error disconnecting session:", err);
        }
        session = null;
      }
    });

    ws.on("error", (err) => {
      console.error("[ws] websocket error:", err);
    });

    try {
      session = await client.createSession({
        model: "gpt-5.4",
        streaming: true,
        onPermissionRequest: approveAll,
      });
      console.log("[ws] copilot session created");

      session.on("assistant.message_delta", (event) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "delta", content: event.data.deltaContent }));
        }
      });

      session.on("session.idle", () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "idle" }));
        }
      });

      sessionReady = true;

      // Process any messages that arrived while session was being created
      for (const msg of pendingMessages) {
        console.log("[ws] processing buffered message");
        await session.send({ prompt: msg });
      }
      pendingMessages.length = 0;
    } catch (err) {
      console.error("[ws] failed to create copilot session:", err);
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "error", message: "Failed to create Copilot session" }));
        ws.close();
      }
    }
  });

  server.listen(PORT, () => {
    console.log(`[server] listening on http://localhost:${PORT}`);
    console.log(`[server] WebSocket available at ws://localhost:${PORT}/ws`);
  });

  // Graceful shutdown
  const shutdown = async () => {
    console.log("\n[server] shutting down...");
    wss.clients.forEach((ws) => ws.close());
    server.close();
    await client.stop();
    console.log("[server] stopped");
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main().catch((err) => {
  console.error("[server] fatal error:", err);
  process.exit(1);
});
