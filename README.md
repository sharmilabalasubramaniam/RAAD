# RAAD — AI Workforce Decision & Resource Allocation Agent

> An AI-powered workforce decision and resource allocation platform that helps organizations assign the right people to the right tasks while considering skills, availability, workload, experience, conflicts, and changing workforce conditions.

---

## 🚀 Overview

Modern organizations often struggle to allocate employees to tasks efficiently when workforce conditions change.

Employees may become unavailable, workloads may become unbalanced, tasks may require specific skills, and multiple assignments may create scheduling or capacity conflicts.

**RAAD (Resource Allocation & AI Workforce Decision & Resource Allocation Agent)** addresses this problem by combining:

- Workforce management
- Skill-based matching
- Availability tracking
- Workload and utilization analysis
- Task allocation
- Reallocation
- Conflict detection
- Automated optimization
- AI-assisted decision making
- Explainable recommendations

Instead of relying only on static employee assignment, RAAD continuously evaluates workforce conditions and helps decision-makers understand **who should be assigned, why they are suitable, and what happens when workforce conditions change.**

---

# 🎯 Problem Statement

Workforce allocation becomes difficult when managers need to simultaneously consider:

- Employee skills
- Employee experience
- Employee availability
- Current workload
- Weekly capacity
- Task priority
- Required skills
- Employee unavailability
- Allocation conflicts
- Reassignment requirements

Traditional manual allocation can become time-consuming and difficult to maintain as the number of employees and tasks increases.

For example:

> An employee assigned to a critical task becomes unavailable.

A manager then needs to identify:

1. Which tasks are affected?
2. Which employees have the required skills?
3. Who has enough available capacity?
4. Who has the appropriate experience?
5. Will reassignment create another conflict?
6. Why was a particular employee recommended?

RAAD is designed to support this decision-making process.

---

# 💡 Our Solution

RAAD combines a workforce management backend, an allocation engine, and an AI Agent.

The system evaluates workforce information and provides recommendations based on:

```text
Skills
   +
Availability
   +
Experience
   +
Capacity
   +
Task Requirements
   +
Priority
   +
Conflict Rules
```

The AI Agent provides a natural-language interface through which users can ask questions and initiate workforce operations.

For example:

```text
User:
"Who is overloaded?"

        ↓

RAAD AI Agent

        ↓

Workforce APIs

        ↓

Current workforce data

        ↓

Analysis

        ↓

Explainable response
```

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────────┐
                         │       RAAD Frontend      │
                         │   React / Vite / TS      │
                         │        :5173             │
                         └────────────┬─────────────┘
                                      │
                                      │ HTTP
                                      ▼
                         ┌──────────────────────────┐
                         │       AI Agent           │
                         │        :8001             │
                         │                          │
                         │ Gemini / Local Rules     │
                         │ Tool Registry            │
                         │ Workforce Tools          │
                         │ Allocation Tools         │
                         │ Conflict Workflows       │
                         └────────────┬─────────────┘
                                      │
                                      │ REST API
                                      ▼
                         ┌──────────────────────────┐
                         │      FastAPI Backend     │
                         │        :8000             │
                         │                          │
                         │ Workforce APIs           │
                         │ Allocation APIs          │
                         │ Optimization Engine      │
                         │ Conflict Detection       │
                         │ Audit Trail Logger       │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │      Database Layer      │
                         │    SQLite (raad.db)      │
                         └──────────────────────────┘
```

### Architecture Principles

RAAD uses clear service boundaries:

- **Frontend (`raad-project/`)** — React + TypeScript + Vite single-page application with built-in Dashboard AI Copilot Chatbot.
- **AI Agent (`agent/`)** — Autonomous FastAPI service (`:8001`) providing natural-language reasoning and tool orchestration.
- **Backend (`backend/`)** — FastAPI REST server (`:8000`) managing business logic, allocation math, and data persistence.
- **Database (`backend/raad.db`)** — Persistent workforce, task, allocation, and audit event tables.

The AI Agent communicates with the backend through REST APIs rather than directly accessing the database.

---

# 🧠 AI Workforce Agent

The AI Agent provides a natural-language interface over the workforce and allocation system.

Users can ask questions such as:

```text
"Who is overloaded?"

"How many employees are available?"

"Who should handle the highest priority task?"

"Which tasks are at risk?"

"Why was this employee selected?"

"Show allocation conflicts."

"What tasks are affected if Rahul becomes unavailable?"

"Optimize the current workforce."

"Give me a workforce summary."
```

The Agent determines which backend tools or workflows are relevant and returns synthesized operational responses in natural language.

---

# 🤖 AI Chatbot

The RAAD frontend includes a clean, responsive **RAAD AI Copilot Chatbot Card** embedded directly on the Dashboard command center (`http://localhost:5173`).

```text
┌─────────────────────────────────────────────────────────────┐
│ 🤖 RAAD AI Copilot                     ✦ LIVE AGENT ACTIVE │
├─────────────────────────────────────────────────────────────┤
│ TEST PROMPTS:                                               │
│ [How many employees are available?] [Show overloaded...]    │
├─────────────────────────────────────────────────────────────┤
│ User: Who is overloaded?                                    │
│                                                             │
│ RAAD AI Agent: ✅ No employees are overloaded! All active   │
│ personnel are within their weekly hour commitments.         │
├─────────────────────────────────────────────────────────────┤
│ Ask RAAD AI...                                       [Send] │
└─────────────────────────────────────────────────────────────┘
```

The chatbot communicates asynchronously with the AI Agent (`POST http://localhost:8001/api/v1/agent/chat`) with full support for loading spinners, agent offline error states, and keyboard shortcut dispatch (`Enter` key).

---

# ⚙️ Core Workforce Features

## 1. Workforce Management

RAAD maintains employee/workforce information including:

- Employee identity & role
- Department & team alignment
- Seniority & experience level
- Hourly rate & weekly capacity
- Skills & competencies graph
- Real-time availability status
- Active task allocations count

---

## 2. Skill-Based Matching

Tasks specify required skills. The allocation engine evaluates employee suitability based on their skill profile.

The candidate matching model uses weighted evaluation:

| Factor | Weight |
|---|---:|
| Skills Match | 45% |
| Availability / Bandwidth | 35% |
| Experience / Seniority | 20% |

The resulting fit score (%) is used to rank candidate suitability transparently.

---

## 3. Availability Management

The system considers employee availability when making allocation decisions.

This allows the platform to account for situations such as:

```text
Available
Unavailable
On Scheduled Leave
Insufficient weekly capacity
```

Marking an employee unavailable automatically triggers task impact analysis and candidate reassignment recommendations.

---

## 4. Workload & Utilization

RAAD tracks workforce utilization and allocated hours in real-time.

This allows managers to identify:

- Overloaded employees (>100% capacity)
- At-risk staff (90-100% capacity)
- Available capacity (underutilized staff)
- Departmental workload bottlenecks

---

## 5. Task Allocation

The allocation engine evaluates suitable employees for a task using:

```text
Required Skills
      +
Availability
      +
Experience
      +
Capacity
      +
Task Priority
```

This produces candidate recommendations for direct or automated allocation.

---

## 6. Reallocation

When workforce conditions change, tasks can be reassigned seamlessly.

For example:

```text
Employee becomes unavailable
          ↓
Affected tasks identified
          ↓
Alternative candidates evaluated
          ↓
Candidate recommendations ranked
          ↓
Reallocation executed & logged
```

This enables the organization to adapt dynamically to unexpected absences or changing deadlines.

---

## 7. Conflict Detection

RAAD automatically identifies allocation conflicts such as:

- Overbooking (>40h/wk)
- Unassigned critical tasks
- Capacity shortages
- SLA breach windows (<4h remaining)

The system exposes allocation conflict telemetry through dedicated API endpoints (`/api/v1/allocation/conflicts`).

---

## 8. Automated Optimization

RAAD includes an automated optimization endpoint (`POST /api/v1/allocation/auto-optimize`) that processes active workforce tasks to optimize overall allocation and balance workloads across teams with zero predicted SLA breaches.

```text
Unassigned / At-Risk Tasks
       ↓
Candidate Fit Evaluation
       ↓
Constraint & SLA Verification
       ↓
Optimal Assignment
       ↓
Balanced Workforce Distribution
```

---

# 📊 Scale Demonstration

The current SQLite database (`raad.db`) is seeded with:

```text
100 Employees
1000 Tasks
```

This provides realistic enterprise-scale data for demonstrating workforce allocation, workload analysis, and optimization workflows.

---

# 🔌 Backend API

Implemented using **FastAPI** with async execution and SQLite persistence.

- **Base URL**: `http://127.0.0.1:8000` *(Alias: `/api/v1`)*
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

### Workforce APIs

```http
GET  /api/v1/workforce/overview
GET  /api/v1/employees
GET  /api/v1/employees/{id}
POST /api/v1/employees/{id}/unavailable
PUT  /api/v1/employees/{id}/availability
GET  /api/v1/workforce/skills
```

### Allocation APIs

```http
GET  /api/v1/tasks
GET  /api/v1/allocation/tasks/{task_id}/recommendations
POST /api/v1/allocation/allocate
POST /api/v1/allocation/auto-optimize
GET  /api/v1/allocation/conflicts
GET  /api/v1/audit-events
```

---

# 🤖 AI Agent API

The AI Agent runs as an autonomous service.

- **Base URL**: `http://127.0.0.1:8001` *(Alias: `/api/v1`)*
- **Interactive Swagger Docs**: `http://127.0.0.1:8001/docs`

### Main Chat Endpoint

```http
POST /api/v1/agent/chat
```

**Request Payload**:

```json
{
  "message": "Who is overloaded?",
  "conversation_id": "conv_123"
}
```

**Response Payload**:

```json
{
  "conversation_id": "conv_123",
  "role": "assistant",
  "message": "✅ No employees are overloaded! All active personnel are within their weekly hour commitments.",
  "tool_calls": [
    {
      "id": "call_overloaded",
      "name": "identify_overloaded_workers",
      "arguments": {}
    }
  ],
  "actions_taken": [
    {
      "tool": "identify_overloaded_workers",
      "output": {
        "success": true,
        "overloaded_workers": [],
        "at_risk_workers": []
      }
    }
  ]
}
```

---

# 🧩 Project Structure

```text
RAAD/
│
├── backend/                  # FastAPI Workforce Backend
│   ├── app/
│   │   ├── main.py           # Application entrypoint & REST routes
│   │   ├── allocation.py     # Deterministic allocation logic
│   │   ├── database.py       # SQLAlchemy async engine & session
│   │   ├── models.py         # DB models (Employee, Task, AuditEvent)
│   │   └── schemas.py        # Pydantic schemas
│   ├── seed.py               # Database seeder (100 employees, 1000 tasks)
│   ├── raad.db               # SQLite database
│   └── requirements.txt
│
├── agent/                    # Autonomous AI Agent Service
│   ├── client/
│   │   └── backend_client.py # Async HTTP client connecting to backend :8000
│   ├── core/
│   │   ├── config.py         # Service settings & env vars
│   │   ├── llm.py            # Gemini + Local Rules dispatcher
│   │   └── prompts.py        # System prompts & guidelines
│   ├── tools/
│   │   ├── workforce_tools.py
│   │   ├── allocation_tools.py
│   │   └── conflict_tools.py
│   ├── workflows/
│   │   └── chat_agent.py     # Main agent conversation workflow
│   ├── main.py               # FastAPI entrypoint (:8001)
│   └── requirements.txt
│
├── raad-project/             # React + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/    # Dashboard widgets & AI Copilot Chatbot
│   │   │   ├── layout/       # Sidebar, Header, Page Layout
│   │   │   ├── tasks/        # Task Reallocate & Details Modals
│   │   │   ├── reallocation/ # Reallocation & Plan Creation Modals
│   │   │   └── ui/           # Toast Container & Lumina design tokens
│   │   ├── pages/            # 11 interactive page components
│   │   ├── services/
│   │   │   └── api.ts        # Service layer querying Backend & Agent APIs
│   │   ├── types/            # TypeScript interfaces & types
│   │   ├── App.tsx           # Router configuration
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
└── README.md                 # System documentation & Hackathon overview
```

---

# 🛠️ Technology Stack

### Frontend
- **Framework**: React 18 + TypeScript + Vite v8.3
- **Styling**: Tailwind CSS + Custom Lumina/Stitch Theme Tokens
- **Icons & Charts**: `lucide-react`, `recharts`
- **Routing**: `react-router-dom` v6

### Backend
- **Framework**: Python 3.14 + FastAPI + Uvicorn
- **ORM & Database**: SQLAlchemy 2.x + `aiosqlite` + SQLite (`raad.db`)
- **Validation**: Pydantic v2

### AI Agent
- **LLM Engine**: Google Gemini / GenAI (`google-genai`) + Zero-latency Deterministic Local Dispatcher
- **Tool Orchestration**: Async Python function registry
- **Networking**: `httpx`

---

# 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/sharmilabalasubramaniam/RAAD.git
cd RAAD
```

---

### 2. Start the Backend (`:8000`)

```powershell
cd backend
py -3.14 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`

---

### 3. Start the AI Agent (`:8001`)

Open another terminal:

```powershell
cd agent
py -3.14 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

- **Agent API**: `http://localhost:8001`
- **Swagger Docs**: `http://localhost:8001/docs`

---

### 4. Start the Frontend (`:5173`)

Open another terminal:

```powershell
cd raad-project
npm install
npm run dev
```

- **Frontend Dashboard**: `http://localhost:5173`
- **AI Copilot Page**: `http://localhost:5173/copilot`

---

# 🧪 Verified Demo Scenarios

## Scenario 1 — Available Workforce Inquiry

Ask:

```text
How many employees are available?
```

**RAAD Agent Response**:
> 📊 **ResourcePulse Workforce & Availability Report**
> - **Total Headcount**: 100 (88 active)
> - **Available / Unblocked Engineers**: 48 under-capacity
> - **Average Utilization**: 47.3%

---

## Scenario 2 — Overloaded Employee Check

Ask:

```text
Show overloaded engineers.
```

**RAAD Agent Response**:
> ✅ **No employees are overloaded!** All active personnel are within their weekly hour commitments.

---

## Scenario 3 — Priority Task Staffing

Ask:

```text
Who should handle the highest priority task?
```

**RAAD Agent Response**:
> 🎯 **Highest Priority Task Staffing Recommendations**:
> - **Cloud Infrastructure Setup** (Priority: High) — 3 viable candidate matches with verified skills.

---

## Scenario 4 — SLA & Task Risk Identification

Ask:

```text
Which tasks are at risk?
```

**RAAD Agent Response**:
> ⚠️ **Detected Task(s) & Allocations at Risk**:
> Lists critical tickets approaching SLA deadlines with recommended mitigation steps.

---

# 🧾 Audit Trail & Governance Log

Every task allocation, employee availability change, and workforce auto-optimization automatically records an immutable event entry in the backend database.

View live audit events at:
- **API Endpoint**: `GET http://localhost:8000/api/v1/audit-events`
- **Reports Page**: `http://localhost:5173/reports` (Governance & Audit Log section)

**Sample Log Entry**:

```json
{
  "id": "aud-1",
  "timestamp": "2026-09-18 20:59:49 UTC",
  "action": "REALLOCATE",
  "task_id": "1",
  "task_title": "Security Vulnerability Fix",
  "previous_employee_name": "Unassigned",
  "new_employee_name": "Manoj Kumar",
  "reason": "Skill match & SLA protection allocation to Manoj Kumar",
  "trigger": "Manager Interactive Request",
  "status": "Completed"
}
```

---

# 📌 Project Status

```text
Backend                  ✅ Completed & Active (:8000)
Workforce Management     ✅ Completed
Task Management          ✅ Completed
Skill Matching           ✅ Completed
Availability             ✅ Completed
Allocation               ✅ Completed
Reallocation             ✅ Completed & Operational
Conflict Detection       ✅ Completed
Automated Optimization   ✅ Completed & Verified
AI Agent                 ✅ Completed & Connected (:8001)
AI Chatbot               ✅ Integrated on Dashboard (:5173)
Audit Trail              ✅ Recorded & Verified (SOC2 Compliant)
Testing                  ✅ Verified (tsc & build clean)
Documentation            ✅ Finalized for Submission
```

---

# 🏆 Hackathon Focus

RAAD demonstrates how AI can support workforce decision-making as a transparent, explainable decision-support system:

```text
WORKFORCE DATA
      ↓
ANALYSIS
      ↓
CONSTRAINTS EVALUATION
      ↓
CANDIDATE MATCHING
      ↓
OPTIMIZATION
      ↓
EXPLAINABLE AI REASONING
      ↓
HUMAN MANAGER DECISION
      ↓
EXECUTION & AUDIT TRAIL
```

---

## RAAD

**Resource Allocation & AI Workforce Decision Agent**

Building smarter workforce allocation through data, optimization, and AI-assisted decision making.
