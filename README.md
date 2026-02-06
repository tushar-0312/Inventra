# 📦 Inventra - AI-Powered Inventory Management

A smart inventory management system using LangGraph multi-agent architecture with Google Gemini AI.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=flat)

## Features

- **Multi-Agent System** - Supervisor, Data, Weather, and Decision agents
- **Weather-Aware Forecasting** - Demand predictions based on weather
- **Smart Recommendations** - AI-generated reorder suggestions
- **Ticket Generation** - Automated procurement tickets

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/inventra.git
cd inventra

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Initialize database
python -c "import sqlite3; conn = sqlite3.connect('inventra.db'); f = open('database/seed.sql', 'r'); conn.executescript(f.read()); conn.commit()"

# Run the app
streamlit run app.py
```

## Architecture

```
User Query → Supervisor → Data/Weather/Decision Agents → Response
```

## License

MIT
