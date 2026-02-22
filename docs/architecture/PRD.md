# AutoApply --- Product Requirements Document (v0.2)

## 1. Vision

AutoApply is a local-first, human-in-the-loop job application assistant
designed for Software Engineering roles.

The system enables users to: - Capture job postings directly from
LinkedIn via a Chrome extension - Store and track applications locally -
Generate truthful, tailored resume PDFs per job - Review changes before
applying - Maintain a structured application pipeline

The system never auto-submits applications and never fabricates
information.

------------------------------------------------------------------------

## 2. Target User

Initial MVP user: Single developer (local environment)

Primary role focus: Software Engineering roles

------------------------------------------------------------------------

## 3. Core Workflow

1.  User opens LinkedIn job page.
2.  User clicks "Capture Job" in Chrome extension.
3.  Extension sends job data to local backend.
4.  Application + JobPosting record created.
5.  User clicks "Generate Tailored Resume".
6.  System analyzes job description against user profile.
7.  Resume PDF is generated and stored.
8.  User manually submits application.

------------------------------------------------------------------------

## 4. Functional Goals

-   Store job postings with full text
-   Track application statuses
-   Generate tailored resume PDFs
-   Maintain resume version history
-   Provide explanation of resume changes
-   Preserve truth constraints

------------------------------------------------------------------------

## 5. Non-Goals (MVP)

-   No automated job crawling
-   No automated form submission
-   No CAPTCHA bypassing
-   No falsified qualifications
-   No multi-user support

------------------------------------------------------------------------

## 6. Success Metrics

Technical: - \>95% successful job captures - PDF renders without
formatting errors - Zero unsupported claims

Outcome: - Reduced time-to-apply - Improved interview response rate
