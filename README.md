# Hermeticav2

## Overview
Hermeticav2 is a framework for Large Language Model (LLM) reasoning, ontology generation, and evaluation. It provides an automated pipeline for extracting, validating, and analyzing structured knowledge (such as ChEBI data) using LLMs, alongside tools for semantic analysis and reasoning validation.

## Project Structure

- **`src/`**: Core source code modules.
  - `evaluation/`: Metrics and evaluation logic.
  - `llm/`: LLM integration and interaction.
  - `ontology/`: Ontology annotation and relationship extraction (`Relations.py`).
  - `pipeline/`: End-to-end processing pipelines (e.g., `ChEBIPipeline.py`).
  - `reasoning/`: Modules for LLM feedback, ontology validation, and formulization.
- **`scripts/`**: Utility scripts for data annotation (`AnnotateAnoLLM.py`, `AnnotateQsNoLLM.py`), scoring (e.g., ROUGE), and semantic analysis.
- **`notebooks/`**: Jupyter notebooks for exploratory data analysis, visualization, and semantic analysis.
- **`data/`**: Datasets used for processing and evaluation.
- **`models/`**: Local model storage and configurations.
- **`results/` & `testing/`**: Output metrics, logs, generated figures, and test suites.
- **`paper/`**: Artifacts, radar charts, and figures generated for publication.
- **`QAEval/`**: Quality assurance and evaluation components.

## Environment Setup

The project uses Conda and Apptainer (Singularity) for environment management, and supports local model execution via Ollama.

### Conda Environment
A Conda environment file is provided to install the necessary Python dependencies:
```bash
conda env create -f Hermenvironment.yml
conda activate Hermetica
```

### Apptainer Container
An `apptainer.def` file is included to build a fully containerized environment with all dependencies pre-installed, including Ollama for local LLM inference.
