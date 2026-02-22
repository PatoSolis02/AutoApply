# AutoApply --- Implementation Guidance

## Purpose

This document defines architectural guardrails and flexibility zones for
implementation.

The goal is to provide strong system constraints while allowing
intelligent architectural decision-making during development.

------------------------------------------------------------------------

## 🔒 Non-Negotiable System Invariants

The following principles must not be violated:

1.  Human-in-the-loop workflow (no automated submission).
2.  No fabricated resume content.
3.  Every generated resume version must be stored.
4.  LinkedIn capture must be user-initiated.
5.  Local-first architecture for MVP.
6.  Clear modular separation between:
    -   Job capture
    -   Application tracking
    -   Resume tailoring
    -   PDF generation
    -   Audit/logging

These define the system's integrity and trust boundary.

------------------------------------------------------------------------

## 🟡 Flexible Implementation Zones

Within the constraints above, implementation decisions may vary.

You may decide:

-   ORM vs raw SQL
-   Exact folder structure
-   Resume internal JSON schema design
-   Keyword extraction strategy
-   Fit scoring methodology
-   PDF generation implementation details
-   Whether to use background workers in MVP
-   Frontend component organization

Improvements are encouraged if they maintain compatibility with system
invariants.

------------------------------------------------------------------------

## 🧠 Architectural Intent

The system should prioritize:

-   Maintainability
-   Extensibility
-   Clear separation of concerns
-   Auditability
-   Deterministic data storage
-   Safety over automation

Avoid overengineering in MVP but design with scalability in mind.

------------------------------------------------------------------------

## 🔎 Design Change Protocol

For significant structural changes:

-   Propose the change before implementation.
-   Justify why it improves the system.
-   Ensure no core invariant is violated.

------------------------------------------------------------------------

## 🚫 Explicitly Forbidden

The system must never:

-   Auto-apply to jobs without explicit user approval.
-   Introduce fabricated experience, skills, employers, or credentials.
-   Bypass platform protections or scrape at scale.
-   Remove version history of resume artifacts.
-   Collapse modules into tightly coupled logic.

------------------------------------------------------------------------

## 🎯 Outcome Objective

Produce a system that is:

-   Safe
-   Traceable
-   Modular
-   Iteratively improvable
-   Architecturally clean

The documents in `/docs` define direction, not rigid implementation
constraints.

You are empowered to optimize the implementation within these
boundaries.
