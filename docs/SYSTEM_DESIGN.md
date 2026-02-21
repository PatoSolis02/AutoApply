# AutoApply --- System Design (Local MVP)

## High-Level Architecture

LinkedIn Page → Chrome Extension → FastAPI Backend (localhost) → SQLite
Database → PDF Artifact Storage → React Dashboard

------------------------------------------------------------------------

## Components

### 1. Chrome Extension (Manifest v3)

-   Extract job title, company, location, description, URL
-   POST to backend endpoint

### 2. Backend (FastAPI)

Responsibilities: - Application CRUD - Job parsing and structuring -
Resume tailoring engine - PDF generation - Audit logging

### 3. Database (SQLite)

-   Zero-config local development
-   Easy migration to Postgres

### 4. PDF Pipeline

-   Structured resume JSON
-   Render HTML template
-   Convert HTML → PDF
-   Store artifact path

### 5. Frontend (React + Vite)

-   Application List
-   Application Detail
-   Resume Version History
-   Profile Editor

------------------------------------------------------------------------

## Design Principles

-   Human-in-the-loop
-   Truth-bound generation
-   Auditability
-   Local-first simplicity
-   Modular architecture
