# AmbitionBox Analysis — Baseline

## Baseline

This document records the state of the project before the AmbitionBox Analysis 2.0 refactor.

## Current application

- Flask web application
- Pandas / NumPy data processing
- Interactive company explorer
- Interactive analytics dashboard
- Company comparison
- CSV export
- JSON API endpoints

## Main pages

- `/` — Home
- `/explore` — Company explorer
- `/dashboard` — Analytics dashboard
- `/compare` — Company comparison
- `/about` — Project information

## API endpoints

- `/api/meta`
- `/api/companies`
- `/api/analytics`
- `/api/export`
- `/api/compare`

## Dataset

The application currently uses `ambitionbox_app/data/companies.csv`.

## Purpose

This baseline is a safety checkpoint. Future refactoring should preserve existing functionality unless a change is explicitly part of the roadmap.
