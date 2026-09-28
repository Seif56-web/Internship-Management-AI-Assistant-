# 🤖 Conversational AI Assistant — Internship Management Platform

An AI-powered conversational assistant integrated into an internship management platform developed during an engineering internship at **Hutchinson**.

The assistant allows users to interact with internship management data and documentation through natural-language queries. It combines **database querying**, **Retrieval-Augmented Generation (RAG)**, and a locally hosted **Large Language Model (LLM)** to provide contextual and relevant responses.

---

## 📌 Project Overview

Managing internship information often requires navigating between structured application data and unstructured documentation.

This project aims to simplify this interaction by integrating a conversational AI assistant directly into the internship management platform.

Instead of manually searching through databases or documents, users can ask questions using natural language, such as:

> "Combien de stagiaires sont enregistrés ?"

> "Quels stagiaires sont validés ?"

> "Que dit la documentation concernant les attestations de stage ?"

> "D'après la proposition, quelle est l'architecture de l'assistant conversationnel ?"

The assistant determines the appropriate information source and generates a response based on the available data.

---

## 🎯 Objectives

The main objectives of the project are:

- Integrate a conversational AI assistant into the existing internship management platform.
- Enable natural-language interaction with internship data.
- Retrieve information from the application database.
- Retrieve relevant information from internship-related documents.
- Implement a Retrieval-Augmented Generation (RAG) pipeline.
- Combine structured database information with unstructured documents when required.
- Provide contextual and source-grounded responses.
- Run the LLM locally using Ollama.

---

## 🏗️ System Architecture

The assistant follows a multi-component architecture:

```text
                    ┌──────────────────────┐
                    │       User           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │  Chatbot Interface   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     FastAPI API      │
                    │  Chatbot Controller  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Intent / Query     │
                    │      Routing         │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       ┌───────────┐     ┌────────────┐    ┌────────────┐
       │ DATABASE  │     │    RAG     │    │   HYBRID   │
       │  Queries  │     │ Retrieval  │    │   Query    │
       └─────┬─────┘     └─────┬──────┘    └─────┬──────┘
             │                 │                 │
             │                 ▼                 │
             │          ┌──────────────┐         │
             │          │ Vector Store │         │
             │          │  ChromaDB    │         │
             │          └──────┬───────┘         │
             │                 │                 │
             │                 ▼                 │
             │          ┌──────────────┐         │
             │          │ Sentence     │         │
             │          │ Transformers │         │
             │          └──────┬───────┘         │
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Ollama          │
                    │       Qwen3          │
                    │        LLM           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Generated Response  │
                    └──────────────────────┘
