# Grant Writer Agent

A sophisticated AI-powered agent built with LangGraph and LangChain that assists organizations in writing high-quality grant proposals, tender documents, and donor-facing submissions. The agent automates the entire proposal writing workflow from document analysis to final submission-ready documents.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Environment Setup](#environment-setup)
- [Running the Agent](#running-the-agent)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Tools & Capabilities](#tools--capabilities)
- [Workflow](#workflow)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Development](#development)

## Overview

The Grant Writer Agent is designed to help organizations create submission-ready grant proposals and tender documents that are:
- **Rooted in logic and feasible** - Based on thorough analysis and research
- **Aligned with international donor standards** - Compliant with donor requirements
- **Based on intensive research** - Leverages uploaded documents and company information
- **Fully detailed** - Complete explanations, never just bullet points

The agent supports multiple organizations (Bayes, Verst Carbon, Ignis Innovation, AFCEN) and can dynamically select LLM models based on user preferences.

## Features

### Core Capabilities

- **Document Analysis**: Automatically analyzes uploaded documents (ToRs, RFPs, templates, compliance guidelines) and extracts key requirements, deadlines, and compliance rules
- **Document Generation**: Generates complete, submission-ready documents using two modes:
  - **Open Generation**: Creates documents from scratch using internal templates and reference documents
  - **Fill Template**: Fills uploaded forms and templates with required information
- **Document Querying**: Answers questions about generated documents and identifies what needs editing
- **Document Editing**: Creates targeted edits with approval workflow - edits are reviewed before applying
- **Document Management**: Delete generated documents and manage artifacts
- **Company Information**: Retrieves organization details, team CVs, past projects, and credentials
- **Task Management**: Creates and manages task lists with automatic progression through pending tasks
- **Intelligent Planning**: Uses reflection and analysis tools to plan methodology and approach

## Environment Setup

### Required API Keys

The agent requires several API keys to function properly. Set up your environment variables by following these steps:

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** and add your API keys:

   ```env
   OPENAI_API_KEY="your_openai_api_key_here"
   GEMINI_API_KEY="your_gemini_api_key_here"
   TAVILY_API_KEY="your_tavily_api_key_here"
   LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
   LANGSMITH_API_KEY="your_langsmith_api_key_here"
   LANGSMITH_TRACING=true
   LANGSMITH_PROJECT="bayes_agents"
   ```

### Required APIs

The following APIs are required for the agent to function:

#### 1. **OpenAI API** (Required)
- **Purpose**: Primary LLM provider for document generation and agent reasoning
- **Get your key**: https://platform.openai.com/api-keys
- **Usage**: Used for all LLM operations including document writing, analysis, and tool calling

#### 2. **Google Gemini API** (Optional but Recommended)
- **Purpose**: Alternative LLM provider option
- **Get your key**: https://makersuite.google.com/app/apikey
- **Usage**: Can be selected as an alternative LLM model

#### 3. **Tavily API** (Optional)
- **Purpose**: Web search and research capabilities
- **Get your key**: https://tavily.com/
- **Usage**: Used for conducting research and gathering context for proposals

#### 4. **LangSmith API** (Optional but Recommended)
- **Purpose**: Tracing, debugging, and monitoring agent behavior
- **Get your key**: https://smith.langchain.com/
- **Usage**: 
  - `LANGSMITH_ENDPOINT`: LangSmith API endpoint (default: https://api.smith.langchain.com)
  - `LANGSMITH_API_KEY`: Your LangSmith API key
  - `LANGSMITH_TRACING`: Enable/disable tracing (set to `true` for development)
  - `LANGSMITH_PROJECT`: Project name for organizing traces (default: "bayes_agents")

### Getting API Keys

1. **OpenAI**: Sign up at https://platform.openai.com/ and navigate to API Keys section
2. **Google Gemini**: Visit https://makersuite.google.com/ and create an API key
3. **Tavily**: Sign up at https://tavily.com/ and get your API key from the dashboard
4. **LangSmith**: Sign up at https://smith.langchain.com/ and create an API key from settings

### Notes

- The `.env` file is already in `.gitignore` and will not be committed to the repository
- Never share your API keys or commit them to version control
- For production deployments, use secure environment variable management (e.g., AWS Secrets Manager, Azure Key Vault)
- LangSmith tracing is recommended for development but can be disabled in production to reduce overhead

## Running the Agent

### Local Development (Python 3.13)

Run the agent locally using LangGraph dev server:

```bash
langgraph dev
```

Once the server is running, you can access:

- 🚀 **API**: http://127.0.0.1:2024
- 🎨 **Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 **API Docs**: http://127.0.0.1:2024/docs

### Docker Deployment

Run the agent using Docker Compose:

```bash
docker compose up
```

When using Docker, the base URL changes to:

- **Base URL**: http://localhost:8000
- 🚀 **API**: http://localhost:8000
- 🎨 **Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

