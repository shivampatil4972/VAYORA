# VAYORA

> **AI-Powered Intelligent Intercity Shared Mobility Platform**

**Research Title:** VAYORA: An AI-Driven Two-Sided Matching, Reliability, Recovery and EV-Aware Framework for Intercity Shared Mobility

---

## 🎯 Core Objective

Traditional shared mobility: **FIND → BOOK → TRAVEL**

VAYORA: **PREDICT → MATCH → OPTIMIZE → BOOK → PREDICT FAILURE → PREPARE BACKUP → RECOVER → MONITOR → COMPLETE → LEARN**

**Primary Research KPI:** Completed Rides per 100 Searches = (Completed Rides / Total Searches) × 100

---

## 🏗 Architecture

```
                    VAYORA
                       |
        +--------------+--------------+
        |                             |
    FRONTEND                     REAL-TIME
 React + TypeScript          Node.js + Socket.IO
        |                             |
        +--------------+--------------+
                       |
                Spring Boot API
                       |
        +--------------+--------------+
        |              |              |
 PostgreSQL/PostGIS   Redis         OSRM
                       |
                Python FastAPI
                       |
        +--------------+--------------+
        |              |              |
   SmartMatch    ReliabilityAI    DemandAI
        |
 Recovery Ranking → Optimization → EV AI → OR-Tools
```

---

## 📁 Project Structure

```
VAYORA/
├── frontend/               React + TypeScript + Vite + Tailwind
├── backend/
│   └── spring-boot/        Java 21 + Spring Boot 3 API
├── ai-service/             Python FastAPI — SmartMatch, ReliabilityAI, DemandAI, EV
├── realtime-gateway/       Node.js + Socket.IO — GPS, live events, chat
├── simulator/              Deterministic simulation engine
├── database/
│   ├── init/               PostgreSQL/PostGIS initialization scripts
│   ├── migrations/         Flyway SQL migrations (added in Module 1)
│   └── osrm/               OSRM map data setup
├── experiments/            B0-B7 experiment framework
├── tests/                  Cross-service integration and E2E tests
├── docs/                   Architecture and API documentation
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- Node.js 20+
- Java 21
- Python 3.11+
- Maven 3.9+

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env and fill in all required values
# NEVER commit .env to version control
```

### 2. Start Infrastructure (PostgreSQL + Redis)

```bash
docker compose up postgres redis -d
```

### 3. Start All Services

```bash
# Option A — Docker Compose (recommended)
docker compose up --build

# Option B — Individual services for development

# Spring Boot
cd backend/spring-boot && mvn spring-boot:run

# FastAPI AI Service
cd ai-service && uvicorn app.main:app --reload

# Node.js Realtime Gateway
cd realtime-gateway && npm run dev

# Frontend
cd frontend && npm run dev
```

### 4. Health Checks

| Service | URL |
|---------|-----|
| Spring Boot | http://localhost:8080/actuator/health |
| FastAPI AI | http://localhost:8000/health |
| Realtime Gateway | http://localhost:3001/health |
| Frontend | http://localhost:5173 |

---

## 🔬 Research Design

### Experiment Baselines (B0–B7)

| Baseline | Feature Set |
|----------|-------------|
| B0 | Basic Search (date, seats, geography) |
| B1 | Rule-Based Matching |
| B2 | SmartMatch (AI matching) |
| B3 | Global Optimization (OR-Tools) |
| B4 | + ReliabilityAI |
| B5 | + DemandAI |
| B6 | + RecoveryMatch |
| B7 | + EV Feasibility |

### Primary KPI

```
Completed Rides per 100 Searches
= (Completed Rides / Total Searches) × 100
```

### Research Question

> "Does progressively adding two-sided matching, reliability prediction, constrained optimization, demand intelligence, recovery intelligence and EV feasibility improve successfully completed shared journeys while maintaining operational constraints and passenger choice?"

---

## 📊 Development Progress

| Phase | Modules | Status |
|-------|---------|--------|
| Phase 1 — Foundation | 0-5 | ✅ Complete (Auth, Users, DB Schema) |
| Phase 2 — Core Mobility | 6-10 | ✅ Complete (Vehicles, Rides, Bookings, Search) |
| Phase 3 — AI Matching | 11-15 | ✅ Complete (SmartMatch B1/B2, ReliabilityAI B4, 18 tests) |
| Phase 4 — Optimization | 16-17 | ✅ Complete (OR-Tools CP-SAT B3, Greedy fallback) |
| Phase 5 — Recovery | 18-20 | ✅ Complete (RecoveryMatch B6, 39 tests total) |
| Phase 6 — Demand Intelligence | 21-24 | ✅ Complete (DemandAI B5, 10 tests) |
| Phase 7 — EV + Sustainability | 25-27 | ✅ Complete (EV Feasibility B7) |
| Phase 8 — Real-Time + Safety | 28-33 | ✅ Complete (WebSocket, Live Location, SOS) |
| Phase 9 — Admin + Research | 34-41 | ✅ Complete (Admin Dashboard API, AI Analytics) |
| Phase 10 — Finalization | 42-46 | ✅ Complete (System Architecture finalized) |

---

## 🔒 Security

- All secrets via environment variables (never hardcoded)
- JWT authentication with refresh tokens (Module 2)
- RBAC: PASSENGER, DRIVER, ADMIN
- Password hashing (BCrypt)
- Rate limiting, CORS, input validation
- SQL injection protection via JPA/Hibernate

## ⚖️ AI Ethics

- AI provides recommendations, never irreversible decisions
- Passenger always retains final choice
- Explainable AI (SHAP) — every recommendation explains why
- No character inferences — only factual metrics
- Clearly labeled predictions vs. guarantees

## 📝 Data Source Labeling

All synthetic/simulation data is explicitly labeled:
- `SIMULATION` — simulator-generated
- `PUBLIC_CALIBRATION` — calibrated from public statistics
- `PILOT` — real-world pilot data (future)

---

## 📚 Documentation

See [`docs/`](docs/) for:
- [Architecture](docs/architecture.md)
- [Database Schema](docs/database.md)
- [API Reference](docs/api.md)
- [AI Pipeline](docs/ai.md)
- [Research Design](docs/research.md)

---

## 🎭 Official Demo Scenario

**Driver:** Kolhapur → Pune, 07:00 AM, 3 seats, ₹400, 20-min max detour  
**Passenger:** Kolhapur → Pune, 07:30 AM, 1 seat

Flow: Search → SmartMatch → ReliabilityAI → OR-Tools → Book →  
*Driver cancels* → RecoveryMatch → Alternative → SafeRide → GPS → Complete → Event Log

---

*VAYORA is a research prototype. Synthetic data must not be represented as real-world results.*
