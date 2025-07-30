<h1 align="center">🧠 Agent Mate</h1>
<p align="center">
  <b>Modular · Event-Driven · AI-Powered</b><br/>
  <i>The cognitive bridge between your world and Omi.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Built%20With-FastAPI-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/AI%20Engine-OpenAI-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Database-PostgreSQL-lightblue?style=flat-square" />
  <img src="https://img.shields.io/badge/Event%20System-Redis-orange?style=flat-square" />
</p>

---

## 🚀 Overview

**Agent Mate** is a highly modular, async-powered backend framework designed for seamless integration with [Omi](https://docs.omi.me/). It enables AI agents to ingest, process, and relay structured information from multiple data sources like Gmail, Notion, and more — delivering it back to Omi in the form of conversations or memories.

---

## 🧠 Key Capabilities

- 🔄 Real-Time & Scheduled Data Collection  
- 🧠 AI-Based Summarization & Classification  
- ⚙️ Dynamic Plugin-based Agent/Subscriber System  
- 🔗 Seamless Omi Memory & Conversation API Integration  
- 🚦 Async Architecture + Redis Event Bus  
- 🔄 Automatic Retry & Rate Limit Management  
- 🔐 OAuth-Based Auth

---

## 🏗️ Architecture

```
AgentMate/
├── Agents/             # Data source agents like Gmail and LLM
├── Connectors/         # External system connectors (e.g., Omi)
├── Core/               # Core logic: EventBus, config, DI, logging, retry
├── DB/                 # Database structure: models, schemas, repos, services
├── Engines/            # AI processing engines (Classifier, Summarizer, Queue, Token tools)
├── Plugins/            # Plugin system interfaces and implementations
├── Routers/            # FastAPI endpoint routers
├── Subscribers/        # Event subscribers / consumers
└── main.py             # Entry point of the application
```

---

## 🔌 Agent Overview

| Agent               | Status | Functionality |
|--------------------|--------|----------------|
| `GmailAgent`        | ✅      | Periodically fetches and classifies emails |
| `OutlookAgent`      | ✅      | Retrieves Outlook emails |
| `NotionAgent`       | 🔜      | Extracts content blocks and page metadata |
| `CalendarAgent`     | 🔜      | Pulls upcoming events |
| `FacebookAgent`     | 🔜      | Reads user feed and messages |
| `InstagramAgent`    | 🔜      | Captures post insights and messages |
| `YouTubeAgent`      | 🔜      | Gathers video metadata and notifications |
| `WhatsAppAgent`     | 🔜      | Parses chat messages for intent and memory |
| `DiscordAgent`      | 🔜      | Listens to server channels and DMs |
| `LinkedInAgent`     | 🔜      | Extracts professional interactions and alerts |

All agents implement the shared `IAgent` interface, and are registered via `AgentFactory`.

---

## 🧪 AI Engine Layer

The NLP processing pipeline supports:

- 📝 **Summarization** (OpenAI, GPT)  
- 🗂️ **Classification**  
- 🧠 **Memory & Conversation Mapping**  
- 🧾 **Intent/NLU & Entity Extraction (NER)**

All processors are pluggable and can be run in parallel using asyncio.

---

## 🔁 Event-Driven System

We utilize **Redis Pub/Sub** to:

- Trigger agents dynamically  
- Communicate between micro-modules  
- Schedule async background jobs  
- Broadcast processed data to WebSocket endpoints

---

## 🧩 Design Patterns

| Pattern     | Purpose |
|-------------|---------|
| **Factory** | Create agents dynamically |
| **Observer**| Manage event subscriptions |
| **Strategy**| NLP engine logic |
| **Adapter** | Normalize 3rd-party APIs |
| **Builder** | Format memory/conversation payloads |
| **DI**      | Plugin/subscriber/service injection |

---

## 🧱 Database Schema

### `user_settings`
| Column        | Type     | Description               |
|---------------|----------|---------------------------|
| uid           | TEXT     | Omi user ID               |
| service_name  | TEXT     | Agent name (gmail, etc.)  |
| service_id    | TEXT     | OAuth/session token key   |
| config        | JSONB    | Agent config JSON         |
| is_logged_in  | BOOLEAN  | Service login status      |

### `processed_data`
| Column        | Type     | Description               |
|---------------|----------|---------------------------|
| uid           | TEXT     | User ID                   |
| service       | TEXT     | Agent name                |
| data_type     | TEXT     | `summary`, `classify`     |
| content       | TEXT     | Final processed result    |

---

## 🧠 Omi Integration

- ✅ Uses [Omi Conversation API](https://docs.omi.me/docs/developer/apps/Import#implementing-the-create-conversation-import)  
- ✅ Uses [Omi Memory API](https://docs.omi.me/docs/developer/apps/Import#implementing-the-create-memories-import)

---

## 🛠️ Setup Guide

### Requirements

- Python 3.9+
- PostgreSQL
- Redis
- Docker (optional)

### Installation

```bash
git clone https://github.com/ibrahimAlbyrk/AgentMate.git
cd AgentMate

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.template .env
# Update .env with your values
```

### Run Server

```bash
python main.py
```

---

## 🧑‍💻 Developer Usage

### Create a New Agent

```python
class MyAgent(IAgent):
    VERSION = AgentVersion(1, 0, 0)

    async def _initialize_impl(self): ...
    async def _run_impl(self): ...
    async def _stop_impl(self): ...
```

### Add a Subscriber

```python
class MySubscriber(BaseSubscriber):
    async def setup(self, event_bus, **services): ...
    async def handle_event(self, data): ...
    async def stop(self): ...
```

---

## 📡 API Reference

### 👤 User Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/settings/` | Create or update user settings |
| `GET`  | `/settings/{uid}/{service_name}` | Fetch user settings for specific service |

### ⚙️ Service Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/{service}/get-settings` | Retrieve merged config (user + default) |
| `POST` | `/{service}/update-settings` | Update user config and restart agent |

### 🔐 Auth System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/{service}/login` | Begin OAuth login |
| `GET`  | `/{service}/callback` | OAuth callback |
| `GET`  | `/{service}/is-logged-in` | Check login state |
| `POST` | `/{service}/login-directly` | Login using known service ID |
| `POST` | `/{service}/logout` | Logout and revoke token |

### 🤖 Agent Status
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/agent/status` | Show currently active agents for user |

### 📩 Gmail API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/gmail/get-email-subjects` | Fetch recent email subjects |
| `POST` | `/gmail/convert-to-memory` | Convert selected/last emails to memory |

### 🔧 Admin Tools
| Method | Endpoint            | Description                                                                     |
|--------|---------------------|---------------------------------------------------------------------------------|
| `GET` | `/admin/user-count` | Return total unique user count                                                  |
| `GET` | `/admin/users-info` | Return total unique user count<br/>and users' services status, logged-in status |
> Info: To use the users-info API, you need to send the x_admin_token info as a query. You can assign from the .env

### 🔄 Composio Webhook
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/composio/webhook` | Webhook listener for composio actions |

### 🧠 Omi Integration
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/setup-complete` | Check if user's setup is complete |

### 🌐 WebSocket
| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS`   | `/ws/{uid}` | WebSocket endpoint for real-time events |

## 📄 License

MIT License – see `LICENSE` file.

---

<p align="center">
  <i>Build AI agents that truly think, act, and integrate — with Agent Mate.</i>
</p>