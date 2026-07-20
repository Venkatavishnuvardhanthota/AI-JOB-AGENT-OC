# AI Job Agent

## Project Summary

Version: 2.0

Status: Design Phase

---

# Overview

AI Job Agent is an intelligent career assistant that automates and simplifies the job application process.

Instead of acting as a traditional job board, the application behaves like an AI employee working on behalf of the user.

Its responsibilities include discovering jobs, evaluating opportunities, generating tailored application materials, preparing applications, tracking progress, and providing actionable insights throughout the hiring journey.

The system combines automation with human oversight to reduce repetitive work while keeping users in control of important decisions.

---

# Vision

Build a production-quality AI platform that helps users obtain employment more efficiently without sacrificing transparency, accuracy, or trust.

The application should become a long-term career companion rather than a one-time resume generator.

---

# Objectives

Primary objectives include:

- Discover relevant job opportunities automatically.
- Match jobs using explainable AI.
- Generate ATS-optimized resumes.
- Generate personalized cover letters.
- Assist with application completion.
- Track every application.
- Provide career analytics.
- Support multiple job providers.
- Support future AI capabilities without architectural redesign.

---

# Core Principles

The product is designed around the following principles:

1. AI First
2. User Control
3. Transparency
4. Explainability
5. Modularity
6. Extensibility
7. Security
8. Reliability
9. Maintainability

---

# Operating Modes

The application supports exactly two execution modes.

## Manual Apply

The user starts the AI manually.

The AI:

- discovers jobs
- evaluates jobs
- researches companies
- prepares resumes
- generates cover letters
- prepares applications

The user may review before submission or allow automatic submission depending on approval settings.

---

## Scheduled Automation

The AI performs the same workflow automatically according to a schedule configured by the user.

Scheduling and approval are independent.

---

# Major Modules

The application contains the following major modules.

## Authentication

Responsible for:

- registration
- login
- security
- sessions

---

## Career Profile

Stores verified user information.

Acts as the single source of truth for AI generation.

---

## Resume Studio

Creates and manages resume versions.

Supports ATS optimization and version history.

---

## Document Management

Stores resumes, cover letters, and uploaded files.

---

## AI Agent

Coordinates the complete workflow.

Responsible for:

- orchestration
- task execution
- retries
- logging

---

## Job Discovery

Searches supported providers.

Normalizes job data.

Removes duplicates.

---

## Match Engine

Evaluates compatibility between user profiles and job descriptions.

Produces explainable scores.

---

## Company Intelligence

Researches employers and summarizes relevant information.

---

## Application Preparation

Generates:

- resumes
- cover letters
- application answers

using verified profile information.

---

## Review Queue

Allows users to review AI-generated applications before submission when manual approval is enabled.

---

## Application Tracker

Tracks applications through their complete lifecycle.

---

## Automation Scheduler

Schedules recurring AI executions.

---

## Notifications

Provides user alerts.

---

## Analytics

Displays performance metrics and career insights.

---

# High-Level Workflow

Career Profile

↓

Job Discovery

↓

Job Matching

↓

Company Research

↓

Resume Selection

↓

Resume Generation

↓

Cover Letter Generation

↓

Application Preparation

↓

Review

↓

Submission

↓

Tracking

↓

Analytics

---

# Technology Stack

Frontend

- React
- TypeScript
- Vite

Backend

- FastAPI
- Python

Database

- PostgreSQL

Browser Automation

- Playwright

AI

- Provider-agnostic abstraction layer

Deployment

- Docker

---

# Documentation Structure

Refer to README.md for the complete documentation index.

---

# Intended Audience

This documentation is intended for:

- Developers
- AI Coding Agents
- Reviewers
- Future Contributors
- Maintainers

---

# Source of Truth

Behavior is defined by the documentation before implementation.

Implementation should conform to documented requirements unless intentionally updated.

---

End of Document