/**
 * VAYORA Realtime Gateway — Entry Point
 * Socket.IO server for GPS streaming, live trip events, chat, notifications.
 */
import express from "express";
import { createServer } from "http";
import { Server as SocketIOServer } from "socket.io";
import winston from "winston";

const PORT = parseInt(process.env.REALTIME_PORT || "3001", 10);
const CORS_ORIGINS = (process.env.CORS_ORIGINS || "http://localhost:5173").split(",");

// Logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [new winston.transports.Console()],
});

// Express app
const app = express();
app.use(express.json());

// Health check
app.get("/health", (_req, res) => {
  res.json({
    status: "UP",
    service: "vayora-realtime-gateway",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
  });
});

// HTTP server
const httpServer = createServer(app);

// Socket.IO server
const io = new SocketIOServer(httpServer, {
  cors: {
    origin: CORS_ORIGINS,
    methods: ["GET", "POST"],
    credentials: true,
  },
  transports: ["websocket", "polling"],
});

// Connection handling (skeleton — full implementation in Module 28)
io.on("connection", (socket) => {
  logger.info("Client connected", { socketId: socket.id });

  socket.on("disconnect", (reason) => {
    logger.info("Client disconnected", { socketId: socket.id, reason });
  });

  // Placeholder ping-pong for health verification
  socket.on("ping", () => {
    socket.emit("pong", { timestamp: new Date().toISOString() });
  });
});

// Start
httpServer.listen(PORT, () => {
  logger.info(`VAYORA Realtime Gateway running on port ${PORT}`);
});

export { app, httpServer, io };
