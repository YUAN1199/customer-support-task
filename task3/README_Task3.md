
# Customer Support Task 3: RAG with Safety Guardrails

## Overview
This project implements a modular Retrieval-Augmented Generation (RAG) system with built-in safety guardrails. It demonstrates core components of an agentic support system, including retrieval, reranking, synthesis, and security checks.

## System Architecture
The system is composed of four core components:
1.  **Retriever Agent**: Performs document retrieval and reranking based on query relevance.
2.  **Synthesizer Agent**: Generates a structured answer from retrieved document chunks.
3.  **Safety Agent**: Implements both input and output guardrails to protect against prompt injection, PII leakage, and confidential information disclosure.
4.  **Orchestrator**: The main controller that coordinates all agents, manages the workflow, and handles user interactions.

## Features
- **Retrieval-Augmented Generation**: Fetches relevant information from a predefined knowledge base.
- **Prompt Injection Detection**: Scans user input for common injection patterns.
- **PII Redaction**: Automatically removes sensitive information (e.g., emails) from inputs and outputs.
- **Confidential Information Filtering**: Blocks responses that contain restricted data like internal salary ranges.
- **Structured Workflow**: Clear separation of concerns between retrieval, synthesis, and safety checks.

## How to Run
1.  Save the provided Python code as `support_system.py`.
2.  Run the script:
    ```bash
    python support_system.py
