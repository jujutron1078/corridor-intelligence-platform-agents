# Grant Writer Agent

A sophisticated AI-powered agent built with LangGraph and LangChain that assists organizations in writing high-quality grant proposals, tender documents, and donor-facing submissions. The agent automates the entire proposal writing workflow from document analysis to final submission-ready documents.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
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

