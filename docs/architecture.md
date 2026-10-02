# VAYORA Architecture Document

## 1. High-Level Architecture Overview

VAYORA is built on a modern microservices architecture, splitting operational state management from computationally heavy AI workloads. 

### Key Components

*   **Spring Boot Backend (`backend/spring-boot`)**: The central operational hub. Handles user authentication (JWT), role-based access control, operational data persistence, geospatial queries (via PostGIS), and WebSocket connections for real-time location/SOS features.
*   **AI Service (`ai-service`)**: A fast, asynchronous Python microservice built with FastAPI. It handles complex AI heuristics, prediction, matching engines (SmartMatch), constrained optimization (OR-Tools), DemandAI, and EV Feasibility tracking.
*   **PostgreSQL (PostGIS)**: The primary operational database storing users, rides, and vehicles.
*   **Redis**: Used as a fast, in-memory cache and message broker for WebSockets.
*   **React Frontend**: (Drafted) to communicate via REST to the backend and WebSocket for live updates.

---

## 2. Communication Flow

1.  **Frontend → Backend**: The frontend communicates via REST (port 8080) for all state changes (e.g., creating a ride, booking a seat).
2.  **Backend → AI Service**: For AI-driven features (e.g., scoring rides, recovery optimization), the Spring Boot backend acts as a client. It delegates to the AI service (port 8000) using asynchronous HTTP requests (WebClient).
3.  **Real-Time Data**:
    *   Drivers stream location updates via WebSockets directly to the Spring Boot application (`/app/location`).
    *   Spring Boot broadcasts these coordinates to subscribed passengers over `topic/ride.{id}`.
    *   SOS triggers follow the same WebSocket broadcasting mechanism to alert users and admins instantaneously.

---

## 3. Data Flow & Persistence

*   **Operational State**: Stored in standard relational tables (e.g., `users`, `rides`, `bookings`). Geometries are stored as PostGIS spatial types (Points/Geographies).
*   **AI Persistence & Research**: All AI predictions are persisted asynchronously by the AI Service into the `ml_predictions` and `event_logs` tables using `asyncpg`. This decouples the heavy write load of analytics from the operational backend.

---

## 4. AI Engine Modules

| Engine | Goal | Methodology |
|--------|------|-------------|
| **SmartMatch (B1/B2)** | Rank optimal rides for passengers | Multi-dimensional heuristic scoring (Distance + Time + Price) |
| **Optimization (B3)** | Global system efficiency | Constraint Programming (OR-Tools CP-SAT) with Greedy Fallback |
| **ReliabilityAI (B4)** | Predict cancellation risk | Bayesian smoothed historical cancellation rates |
| **DemandAI (B5)** | Predict supply gaps | Historical gap analysis & fulfillment rate estimation |
| **RecoveryMatch (B6)** | Re-route on driver cancellation | Scored backup ranking with driver exclusion constraints |
| **EV Feasibility (B7)** | Map energy viability | Consumption calculation based on terrain, speed, and temp |

---

## 5. Security & Ethics

*   **Security**: Secured via stateless JWT authentication. Endpoints are strictly protected via RBAC (Driver vs Passenger vs Admin). Passwords encrypted via BCrypt.
*   **Ethics**: All AI logic strictly adheres to "Recommendations only"—humans always make the final choice. SHAP logic explicitly provides explainability constraints for all models. No sensitive user characteristics are parsed.
