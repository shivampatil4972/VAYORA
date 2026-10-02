/**
 * Module 0 — Realtime gateway health endpoint test.
 */
import request from "supertest";
import { app } from "../src/index";

describe("GET /health", () => {
  it("should return 200 with status UP", async () => {
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("UP");
    expect(res.body.service).toBe("vayora-realtime-gateway");
  });
});
