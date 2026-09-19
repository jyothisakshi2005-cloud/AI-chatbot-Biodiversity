# Darukaa.Earth — System Architecture & Scientific Methodology

## Architectural Overview

Darukaa.Earth implements a decoupled, modular environmental intelligence platform designed to model complex ecological systems without hallucination.

```
+-------------------------------------------------------------------------+
|                              Frontend (Vite / React 19)                 |
|  - Scientific Chat View (Multi-Turn Dialogue & Context Pills)           |
|  - 5-Section Environmental Intelligence Dashboard                       |
|  - Ecological Evidence & Knowledge Base Explorer                        |
|  - Structured Input & JSON Importers                                    |
+------------------------------------+------------------------------------+
                                     |
                          HTTPS REST API (JSON)
                                     |
+------------------------------------v------------------------------------+
|                           FastAPI Application Gateway                   |
|  - /api/chat                  - /api/analyze                            |
|  - /api/recommendations       - /api/environmental-profile              |
|  - /api/knowledge/search      - /api/metrics/{profile_id}               |
|  - /api/evidence/{id}         - /api/scenarios                          |
+------------------------------------+------------------------------------+
                                     |
       +-----------------------------+-----------------------------+
       |                             |                             |
+------v---------------------+ +-----v---------------------+ +-----v---------------------+
|    Conversation Manager    | |  Environmental Processor  | |    ChromaDB Retriever     |
| - Multi-turn memory        | | - Data completeness meter | | - MiniLM-L6 Embeddings    |
| - Regex/Entity extraction  | | - Multi-domain diagnostics| | - Cosine similarity       |
| - Clarifying question logic| | - Health scoring (0-100)  | | - Metadata citation link  |
+--------------+-------------+ +-------------+-------------+ +-------------+-------------+
               |                             |                             |
               +-----------------------------+-----------------------------+
                                             |
                               +-------------v-------------+
                               |   Multi-Metric Reasoning  |
                               |          Engine           |
                               | (Evaluates >= 3 Variables)|
                               +-------------+-------------+
                                             |
                               +-------------v-------------+
                               |   Recommendation Engine   |
                               | (Specific, Measurable,    |
                               |  Time Horizon, Confidence)|
                               +-------------+-------------+
                                             |
                               +-------------v-------------+
                               |     Evidence Validator    |
                               |  (Anti-Hallucination &    |
                               |   Citation Verification)  |
                               +-------------+-------------+
                                             |
                       +---------------------+---------------------+
                       |                                           |
+----------------------v---------------------+ +-------------------v---------------------+
|           SQLite Database (Relational)     | |           ChromaDB Vector Store         |
| - Users, Conversations, Messages           | | - Chunked peer-reviewed studies         |
| - Profiles, Metrics, Recommendations       | | - FAO reports, IPCC assessments         |
+--------------------------------------------+ +-----------------------------------------+
```

## Ecological Variables Universe
1. **Soil Health**: Organic Carbon %, pH, Moisture %, Bulk Density, Biological Respiration, Microbial Activity.
2. **Land Cover & Use**: Monoculture vs Polycropping, Agroforestry, Linear Corridors, Habitat Fragmentation Index.
3. **Biodiversity**: Species Richness, Pollinator Abundance, Native Taxa Ratio, Trophic Stability.
4. **Climate & Water**: Annual Precipitation, Rainfall Distribution Pattern, Drought Frequency, Thermal Stress.
5. **Human Impact**: Agrochemical Saturation, Intensive Tillage, Historical Deforestation, Buffer Depletion.
