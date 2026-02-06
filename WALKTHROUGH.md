# Inventra - Project Walkthrough

## Overview

**Inventra** is an AI-powered Smart Inventory Management System built with Streamlit and LangGraph. It uses a multi-agent architecture to analyze inventory, forecast weather impact, and generate actionable recommendations.

---

## Setup & Running

### 1. Prerequisites
- Python 3.8+
- Google Gemini API Key

### 2. Environment Setup

```bash
# Copy environment template
copy .env.example .env

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Initialization

The SQLite database must be initialized before first run:

```python
python -c "import sqlite3; conn = sqlite3.connect('inventra.db'); f = open('database/seed.sql', 'r'); conn.executescript(f.read()); conn.commit()"
```

### 4. Run the Application

```bash
streamlit run app.py
```

Access at: http://localhost:8501

---

## Project Structure

```
inventra/
├── app.py                 # Streamlit web interface
├── agents/                # Multi-agent system
│   ├── graph.py          # LangGraph workflow definition
│   ├── supervisor.py     # Routes queries to appropriate agents
│   ├── data_agent.py     # Queries inventory database
│   ├── weather_agent.py  # Fetches weather forecasts
│   └── decision_agent.py # Generates recommendations & tickets
├── database/
│   ├── db.py             # Database utilities
│   └── seed.sql          # Sample inventory data
├── tools/
│   ├── db_tools.py       # LangChain tools for DB queries
│   └── ticket_tools.py   # Mock ticketing system
├── prompts/              # Agent prompt templates
├── .env.example          # Environment template
└── requirements.txt      # Python dependencies
```

---

## Multi-Agent Architecture

```
User Query
    │
    ▼
┌─────────────┐
│ Supervisor  │  → Routes to appropriate agent
└─────────────┘
       │
       ├──────────────┬────────────────┐
       ▼              ▼                ▼
┌────────────┐  ┌─────────────┐  ┌────────────────┐
│ Data Agent │  │Weather Agent│  │ Decision Agent │
└────────────┘  └─────────────┘  └────────────────┘
       │              │                  │
       ▼              ▼                  ▼
  Inventory DB   Weather API      Ticket System
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Inventory Analysis** | Query stock levels, low stock items, category breakdowns |
| **Weather Forecasting** | 7-day forecasts for Mumbai, Delhi, Bengaluru |
| **Smart Recommendations** | AI-generated reorder suggestions based on weather & stock |
| **Ticket Generation** | Mock tickets for procurement actions |

---

## Example Queries

- "What items are low on stock?"
- "How will weather affect sales in mumbai?"
- "Generate reorder recommendations for next week"
- "Show me all umbrella inventory"

---

## Troubleshooting

### Database Error: "unable to open database file"
Run the database initialization command above.

### Encoding Error: "'charmap' codec can't encode character"
This was fixed by replacing Unicode emojis with ASCII alternatives in `tools/db_tools.py` and `tools/ticket_tools.py`.

---

## Configuration

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Required |
| `GEMINI_MODEL` | Model to use | `gemini-2.0-flash-exp` |
| `DATABASE_PATH` | SQLite DB path | `inventra.db` |
| `DEBUG` | Enable verbose logging | `false` |
