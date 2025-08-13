# Reinforcement Learning from Community Feedback (RLCF) - Framework Implementation

Questo repository contiene l'implementazione Python del framework **Reinforcement Learning from Community Feedback (RLCF)**, come descritto nel paper scientifico **RLCF.md**. Il progetto è una piattaforma di ricerca ad alte prestazioni per studiare e validare sistemi di Artificial Legal Intelligence (ALI) attraverso meccanismi di validazione distribuita, dynamic authority scoring e uncertainty-preserving aggregation.

## 📄 Documentazione Scientifica

- **Paper Teorico**: [RLCF.md](RLCF.md) - Framework teorico completo con formule matematiche e algoritmi
- **Implementazione**: Questo repository - Implementazione Python production-ready
- **Connessione Teoria-Pratica**: Ogni modulo del codice referenzia precisamente le sezioni del paper RLCF.md

## 🚀 Caratteristiche Principali

- **🧠 Theoretical Rigor**: Implementazione diretta degli algoritmi descritti in RLCF.md con referenze precise
- **⚡ Architettura Async**: Framework completamente asincrono basato su FastAPI e SQLAlchemy async
- **🔒 Sicurezza**: Valutazione sicura delle formule tramite asteval invece di eval()
- **⚛️ Atomicità**: Operazioni di aggregazione atomiche e resilienti ai fallimenti
- **🧪 Testabilità**: Suite di test completa con pytest e mocking avanzato
- **📏 Code Quality**: Formattazione automatica con Black e linting con Ruff
- **🏗️ Dependency Injection**: Sistema centralizzato di iniezione delle dipendenze
- **🎯 Academic-Ready**: Codice documentato per pubblicazione scientifica e peer review
- **⚖️ Constitutional AI**: Implementa il Constitutional Governance Model (RLCF.md Sezione 5.1)

## Architettura e Workflow dei Componenti

Il framework è costruito su un'architettura modulare che mappa direttamente i concetti teorici del paper in componenti software interagenti. Il workflow principale è orchestrato da un'API FastAPI asincrona che espone la logica di business definita in un livello di servizi atomici.

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Async Layer                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Dependencies  │  │      Main       │  │    Endpoints    │  │
│  │   (DI System)   │  │   (Routing)     │  │   (Handlers)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Async Service Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Task Service   │  │ Post Processing │  │ Bias Analysis   │  │
│  │  (Orchestration)│  │  (Consistency)  │  │  (Detection)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Core Algorithm Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Authority Module│  │ Aggregation     │  │ Task Handlers   │  │
│  │  (Safe Eval)    │  │   Engine        │  │  (Polymorphic)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  Async Database Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   AsyncSession  │  │   Models        │  │   Config        │  │
│  │   (aiosqlite)   │  │ (SQLAlchemy)    │  │  (YAML/Pydantic)│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Configurazione del Modello (`model_config.yaml`)

- **Concetto (Paper):** L'intero modello matematico (pesi, soglie, formule) è parametrizzabile.
- **Implementazione:** Un file `model_config.yaml` definisce tutti i parametri del modello, come i pesi di autorità (α, β, γ), il fattore di decadimento (λ) e le regole per calcolare le credenziali. Questo permette ai ricercatori di testare diverse teorie senza modificare il codice.
- **Modulo Chiave:** `config.py` carica e valida questo file utilizzando Pydantic, rendendo la configurazione accessibile globalmente in modo sicuro.

### 2. Dynamic Authority Scoring (`authority_module.py`) - 🔒 Async & Secure

- **Teoria (RLCF.md):** Dynamic Authority Scoring Model (Sezione 2.1) e Principle of Dynamic Authority (Sezione 1.2)
- **Implementazione:** Motore di calcolo asincrono che implementa le formule matematiche esatte del paper:
  - `calculate_baseline_credentials()`: **RLCF.md Sez. 2.2** - Formula B_u = Σ(w_i · f_i(c_{u,i})) con valutazione sicura asteval
  - `update_track_record()`: **RLCF.md Sez. 2.3** - Exponential smoothing T_u(t) = λ·T_u(t-1) + (1-λ)·Q_u(t)
  - `update_authority_score()`: **RLCF.md Sez. 2.1** - Formula A_u(t) = α·B_u + β·T_u(t-1) + γ·P_u(t)
  - **Sicurezza**: asteval per safe formula evaluation, transazioni atomiche
  - **Constitutional Compliance**: Segue i principi di Auctoritas Dynamica

### 3. Uncertainty-Preserving Aggregation (`aggregation_engine.py`) - ⚡ Algorithm 1 Implementation

- **Teoria (RLCF.md):** Algorithm 1: RLCF Aggregation with Uncertainty Preservation (Sezione 3.1)
- **Implementazione:** Implementazione diretta dell'algoritmo centrale del framework:
  - `calculate_disagreement()`: **RLCF.md Sez. 3.2** - Formula δ = -(1/log|P|) Σ ρ(p)log ρ(p) per Shannon entropy
  - `aggregate_with_uncertainty()`: **RLCF.md Sez. 3.1** - Algorithm 1 completo con threshold τ=0.4
  - `extract_positions_from_feedback()`: **RLCF.md Sez. 3.2** - Position extraction per disagreement quantification
  - `identify_consensus_and_contention()`: **RLCF.md Sez. 3.3** - Expert disagreement analysis
  - **Uncertainty Preservation**: Implementa Principle of Preserved Uncertainty (Incertitudo Conservata)
  - **Dialectical Nature**: Preserva la natura dialettica del ragionamento legale

### 4. Extended Bias Detection Framework - 🔍 6-Dimensional Analysis

- **Teoria (RLCF.md):** Extended Bias Detection Framework (Sezione 4.3) - 6 dimensioni vs 4 teoriche
- **Implementazione Superiore:** Il codice estende la teoria con implementazione avanzata:
  - `bias_analysis.py`: **RLCF.md Sez. 4.3** - Framework completo con formula B_total = √(Σ b_i²)
    - Demographic bias (b1), Professional clustering (b2), Temporal drift (b3)
    - Geographic concentration (b4), Confirmation bias (b5), Anchoring bias (b6)
    - `calculate_authority_correctness_correlation()`: **RLCF.md Sez. 2.1** - Validazione autorità
  - `generate_bias_mitigation_recommendations()`: **RLCF.md Sez. 5.1** - Constitutional compliance
  - `devils_advocate.py`: **RLCF.md Sez. 3.5** - Probabilistic assignment P(advocate) = min(0.1, 3/|E|)
  - **Constitutional Governance**: Bias detection e mandatory disclosure automatici

### 5. Task Orchestration & Constitutional Governance - 🎯 Business Logic Layer

- **Teoria (RLCF.md):** Task Lifecycle Management (Sezione 4.1) e Constitutional Governance Model (Sezione 5.1)
- **Implementazione:**
  - `services/task_service.py`: **RLCF.md Sez. 4.1** - Complete task workflows con orchestrazione atomica:
    - `orchestrate_task_aggregation()`: Decouples business logic da API endpoints
    - `_aggregate_and_save_result()`: **RLCF.md Sez. 3.1** - Algorithm 1 execution
    - `_calculate_and_store_consistency()`: **RLCF.md Sez. 2.3** - Quality metrics Q_u(t)
    - `_calculate_and_store_bias()`: **RLCF.md Sez. 4.3** - 6-dimensional bias detection
  - `task_handlers/`: **RLCF.md Sez. 3.6** - Dynamic Task Handler System (Strategy pattern)
    - 9 legal task types supportati con logica domain-specific
    - Polymorphic architecture per extensibility
  - `training_scheduler.py`: **RLCF.md Sez. 5.2** - Periodic Training Schedule (14-day cycle)
  - **Constitutional AI**: Automated accountability reporting e transparency compliance

## 📚 Connessione Teoria-Implementazione

### Mapping Diretto Paper → Codice

| **RLCF.md Section** | **Modulo Python** | **Funzione/Classe** | **Formula/Algoritmo** |
|---------------------|-------------------|---------------------|----------------------|
| **1.2 - Principi Costituzionali** | `*` | Tutti i moduli | 4 principi fondamentali |
| **2.1 - Dynamic Authority Scoring** | `authority_module.py` | `update_authority_score()` | A_u(t) = α·B_u + β·T_u + γ·P_u |
| **2.2 - Baseline Credentials** | `authority_module.py` | `calculate_baseline_credentials()` | B_u = Σ(w_i · f_i(c_{u,i})) |
| **2.3 - Track Record Evolution** | `authority_module.py` | `update_track_record()` | T_u(t) = λ·T_u(t-1) + (1-λ)·Q_u(t) |
| **3.1 - Algorithm 1** | `aggregation_engine.py` | `aggregate_with_uncertainty()` | Complete algorithm |
| **3.2 - Disagreement Quantification** | `aggregation_engine.py` | `calculate_disagreement()` | δ = -(1/log|P|) Σ ρ(p)log ρ(p) |
| **3.5 - Devil's Advocate System** | `devils_advocate.py` | `DevilsAdvocateAssigner` | P(advocate) = min(0.1, 3/|E|) |
| **3.6 - Dynamic Task Handler** | `task_handlers/` | `BaseTaskHandler` + 9 handlers | Strategy pattern |
| **4.1 - Task Lifecycle** | `services/task_service.py` | `orchestrate_task_aggregation()` | Business logic orchestration |
| **4.3 - Extended Bias Detection** | `bias_analysis.py` | `calculate_total_bias()` | B_total = √(Σ b_i²) - 6 dimensions |
| **5.1 - Constitutional Governance** | `main.py, bias_analysis.py` | Constitutional framework | Algorithmic principles |
| **5.2 - Periodic Training** | `training_scheduler.py` | `PeriodicTrainingScheduler` | 14-day cycle, 4 phases |

### Academic Rigor
- **Docstring References**: Ogni funzione cita precisamente le sezioni RLCF.md
- **Mathematical Precision**: Implementazione esatta delle formule teoriche
- **Algorithmic Fidelity**: Algorithm 1 implementato line-by-line
- **Reproducibility**: Configurazione YAML per esperimenti riproducibili
- **Peer Review Ready**: Codice documentato per submission accademica

## 🧪 Qualità e Testing

Il framework include una suite di test completa e strumenti per garantire la qualità del codice:

### Test Suite
- **Posizione**: `tests/` directory
- **Framework**: pytest con supporto asyncio
- **Copertura**: Test unitari per tutti i moduli core
- **Mocking**: AsyncMock per operazioni database asincrone
- **Esecuzione**: `pytest tests/`

### Strumenti di Qualità
- **Formattazione**: Black per formattazione automatica del codice
- **Linting**: Ruff per analisi statica e rilevamento errori
- **Configurazione**: `pytest.ini`, `dev-requirements.txt`

### Fixtures e Helper
- `conftest.py`: Fixtures comuni per mock di database, utenti, task
- Generatori di dati di test per scenari complessi
- Performance timer per test di performance

### Comandi di Sviluppo
```bash
# Installa dipendenze di sviluppo
pip install -r dev-requirements.txt

# Esegui test
pytest

# Formatta codice
black .

# Lint codice
ruff check . --fix
```

## 🔬 Workflow Sperimentale Scientifico

### Approccio Research-First
Il framework è progettato per supportare ricerca accademica rigorosa con:
- **Riproducibilità Garantita**: Configurazione YAML per parametri sperimentali
- **Data Collection Validata**: Strutture dati ottimizzate per analisi statistica
- **Statistical Power**: Support per power analysis e sample size calculation
- **Export Scientifici**: Dati esportabili in formati standard (CSV, JSON, LaTeX)

### Workflow di Ricerca

1. **🔧 Experimental Design**: Definire ipotesi e parametri in `model_config.yaml` secondo RLCF.md
2. **👥 Community Setup**: Popolare database con partecipanti usando endpoint REST API
3. **📋 Task Creation**: Creare legal tasks con ground truth separation automatica
4. **🔍 Blind Evaluation Phase**: Attivare blind evaluation per prevenire anchoring bias
5. **📊 Data Collection**: Raccogliere feedback con timestamp e metadata per analisi temporali
6. **⚗️ Aggregation Execution**: Eseguire Algorithm 1 con uncertainty preservation automatica
7. **🔬 Statistical Analysis**: Analizzare risultati con metriche di reliability e validity
8. **📈 Bias Assessment**: Generare report bias 6-dimensionali con raccomandazioni
9. **📄 Scientific Export**: Esportare dati in formati publication-ready per peer review
10. **🔄 Iterative Refinement**: Modificare parametri e ripetere per validation e replication

## 🚀 Setup e Installazione

### Requisiti del Sistema
- Python 3.8+
- SQLite (incluso con Python)

### Installazione
1.  **Clona il repository:**
    ```bash
    git clone <repository-url>
    cd RLCF
    ```

2.  **Crea ambiente virtuale (raccomandato):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or
    venv\Scripts\activate     # Windows
    ```

3.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Installa dipendenze di sviluppo (opzionale):**
    ```bash
    pip install -r dev-requirements.txt
    ```

### Avvio dell'Applicazione

**FastAPI Server:**
```bash
uvicorn rlcf_framework.main:app --reload
```

**Gradio Interface:**
```bash
python app_interface.py
```

### Accesso
- **API Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`  
- **Gradio Interface**: `http://127.0.0.1:7860`

### Verifica Installazione e Academic Setup
```bash
# Test core algorithms (Academic validation)
pytest tests/test_authority_module.py tests/test_aggregation_engine.py -v

# Test constitutional compliance
pytest tests/test_bias_analysis.py -v

# Verifica implementazione Algorithm 1
pytest tests/test_uncertainty_preservation.py -v

# Code quality per peer review
ruff check .
black --check .

# Verifica referenze RLCF.md nei docstring
grep -r "References:" rlcf_framework/
```

### 🎓 Academic Usage
```bash
# Genera dataset per pubblicazione
curl -X GET "http://127.0.0.1:8000/export/dataset?format=scientific"

# Esporta metriche per paper
curl -X GET "http://127.0.0.1:8000/metrics/authority_correlation"

# Report bias per methodology section
curl -X GET "http://127.0.0.1:8000/bias/task/1/report"
```

## 📈 Performance Features

- **Async/Await**: Tutte le operazioni database sono asincrone per massime prestazioni
- **Connection Pooling**: Pool di connessioni database ottimizzato
- **Atomic Transactions**: Operazioni atomiche per consistency e resilienza  
- **Lazy Loading**: Caricamento asincrono dei dati secondo necessità
- **Efficient Querying**: Query ottimizzate con SQLAlchemy async

## 🔒 Sicurezza e Constitutional AI

### Sicurezza Tecnica
- **Safe Evaluation**: asteval invece di eval() per valutazione sicura formule (RLCF.md Sez. 2.2)
- **API Key Protection**: Endpoint admin protetti da API key
- **Input Validation**: Validazione Pydantic per tutti gli input
- **SQL Injection Protection**: SQLAlchemy ORM protegge da SQL injection
- **Connection Security**: Connessioni database sicure con parametri controllati

### Constitutional Governance (RLCF.md Sezione 5.1)
- **Transparency Principle**: Tutti i processi sono auditabili e reproducibili
- **Bias Detection**: Mandatory disclosure automatico dei bias rilevati
- **Community Benefit**: Maximization del beneficio della comunità
- **Academic Freedom**: Preservazione della libertà accademica nelle valutazioni
- **Expert Knowledge Primacy**: Primato della conoscenza esperta con oversight democratico

### Accountability Reporting (RLCF.md Sezione 5.3)
- **Automated Reports**: Report di accountability ogni 14 giorni
- **Transparency Metrics**: Metriche complete per ogni ciclo di training
- **Constitutional Compliance**: Validazione automatica dei principi costituzionali
- **Audit Trail**: Tracciabilità completa di tutte le decisioni e processi