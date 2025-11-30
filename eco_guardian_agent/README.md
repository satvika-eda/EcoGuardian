# 🌿 EcoGuardian: Multi-Agent Environmental Health Intelligence

AI-powered environmental and health intelligence built using Google’s ADK.  

---

## 🌍 Problem Statement

Over 150 million Americans live in regions with poor air quality — yet daily health decisions still rely on fragmented tools:

- Weather apps show temperature but not health implications  
- AQI apps show pollution but not symptoms  
- Health sites offer generic advice without environmental context  
- Users often check 4–5 different apps daily

### Why Existing Solutions Fall Short
- Provide raw data, not intelligence
- No correlation between environment → symptoms → outbreaks
- No medical triage contextualized to environmental triggers

---

## 💡 Solution Overview

**EcoGuardian** is an AI-driven, multi-agent environmental health intelligence platform built with Google ADK.

### 🚀 Value Proposition
- 30× faster than manually checking multiple apps  
- Unified analysis across air, weather, pollen, UV, symptoms, outbreaks 
- Smart routing → only the required agents are triggered  
- Real-time outbreak intelligence (WHO, CDC, GDELT)  
- Safety-first medical triage with mandatory disclaimers  

---

## 🏗️ Architecture

![architecture](architecture.png)

### Execution Flow
![EF-1](execution_flow_1.png)

![EF-2](execution_flow_2.png)

````

### Agent Hierarchy

#### 🧠 Root Coordinator (LlmAgent)
- Routes queries to proper agents  
- Maintains `{city: str}` in session state  
- Synthesizes multi-agent responses  

#### 🌎 Environmental Intelligence Agents
- Air Quality Agent (OpenAQ)  
- Weather Agent (Open-Meteo)  
- Pollen Agent (Pollen.com)  
- UV Index Agent (Open-Meteo AQ)  

#### 🏥 Health Intelligence Pipeline
**Stage 1 – Parallel Execution**  
- Symptom Analyzer  
- Outbreak Monitor  

**Stage 2 – Sequential**  
- Hospital Locator  

**Stage 3 – Decision Coordinator**  
- Merges intel into actionable guidance  

#### Events Agent
- Uses google_search tool for environmental/sustainability events  

---

## ✨ Features

### 🌤 Environmental Monitoring
- Real-time AQI + PM2.5, PM10, O₃, NO₂  
- Temperature, humidity, wind, precipitation  
- Pollen levels (tree/grass/weed)  
- UV index + risk analysis  

### 🏥 Health Intelligence
- Disease outbreak detection (WHO, CDC, GDELT)  
- Symptom-based urgency classification (NOT diagnosis)  
- Nearest hospitals with distance + emergency flagging  
- Built-in medical safety guardrails  

### 🧑‍💻 User Experience
- Streamlit UI  
- Persistent session storage (SQLite)  
- Conversation memory  
- Multi-agent orchestration (10 agents)  

---

## 🚀 Installation

### 1. Clone repository
```bash
git clone https://github.com/satvika-eda/EcoGuardian.git
cd EcoGuardian
````

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate    
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add environment variables

Add GOOGLE_API_KEY and OPENAQ_API_KEY

---

## ⚙️ Configuration

### Required

```
GOOGLE_API_KEY=your_key
OPENAQ_API_KEY=your_key
```

### Free APIs used:

* Google Gemini API
* OpenAQ Air Quality API
* Open-Meteo Weather & UV API
* Pollen.com API (unofficial)
* WHO + CDC + GDELT outbreak data
* OpenStreetMap Overpass API

---

## 🎮 Usage

### Run the app

```bash
streamlit run app.py
```

### Example Queries

* "How's the environment in Miami today?"
* "I have fever and cough for 8 days in Boston."
* "Find nearest hospitals."
* "What sustainability events are happening this weekend?"

---

## 🔧 Technical Details

### Tech Stack

| Component     | Technology                                           |
| ------------- | ---------------------------------------------------- |
| Framework     | Google ADK                                           |
| LLM           | Gemini 2.5 Flash Lite                                |
| UI            | Streamlit                                            |
| Database      | SQLite                                               |
| Memory        | InMemoryMemoryService                                |
| Orchestration | LlmAgent, SequentialAgent, ParallelAgent             |
| APIs          | OpenAQ, Open-Meteo, Pollen.com, WHO, CDC, GDELT, OSM |

### Orchestration Patterns

* Independent agents
* Sequential pipelines
* Parallel execution
* Hybrid routing
* Agents wrapped as tools (`AgentTool`)

---

## 🌐 API Integrations

### 🔵 Air Quality — OpenAQ

### ☁️ Weather — Open-Meteo

### 🌾 Pollen — Pollen.com

### 🌞 UV Index — Open-Meteo (Air Quality API)

### 🦠 Outbreaks — WHO, CDC, GDELT, outbreak.info

### 🏥 Hospitals — OpenStreetMap Overpass API

Each API is accessed via an ADK `Tool()` or `AgentTool()`.

---

## 📁 Project Structure

```
ecoguardian/
├── agent.py
├── app.py
├── prompts.py
├── tools/
│   ├── air_quality.py
│   ├── weather.py
│   ├── pollen.py
│   ├── uv_index.py
│   └── disease_outbreak.py
├── ecoguardian_sessions.db
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 🎓 ADK Concepts Implemented

* **Multi-Agent System (10 agents total)**
* **SequentialAgent (3-stage medical pipeline)**
* **ParallelAgent (symptoms + outbreaks)**
* **AgentTool wrappers**
* **Session persistence (SQLite via DatabaseSessionService)**
* **Memory (InMemoryMemoryService)**
* **State management (StateSchema: {city: str})**
* **Observability (LoggingPlugin)**
* **Retry logic for API failures**
* **Medical safety guardrails**

---

## 🏥 Safety & Ethics

### ❗ System NEVER:

* Diagnoses medical conditions
* Recommends treatments
* Provides prescriptions
* Replaces doctors

### ✅ System ALWAYS:

* Adds medical disclaimers
* Flags emergencies
* Encourages professional care
* Avoids PHI storage
* Uses anonymous session IDs only

---

## 🚀 Future Enhancements

### Product Features

* Integrate Google Maps to the UI for better user experience.
* Add more agents for other environmental and health factors

### Technical Improvements

* Caching
* Agent Evaluation Suite
* A2A protocol (Agent-to-Agent)
* Cloud Run / Agent Engine deployment
* Monitoring dashboard (Grafana + Prometheus)

```
