# Route Extraction Protocol
## Safe Process for Moving Routes from main.py to Modular Routers

**Version:** 1.0
**Created:** October 2, 2025
**Last Updated:** October 2, 2025
**Status:** 🔴 DRAFT

---

## Table of Contents

1. [Overview](#overview)
2. [When to Use This Protocol](#when-to-use)
3. [Pre-Extraction Checklist](#pre-extraction)
4. [Extraction Steps](#extraction-steps)
5. [Testing Requirements](#testing-requirements)
6. [Deployment Protocol](#deployment-protocol)
7. [Rollback Plan](#rollback-plan)
8. [Case Studies](#case-studies)
9. [Quick Reference](#quick-reference)

---

## 1. Overview

### Purpose

This protocol provides a **step-by-step, battle-tested process** for safely extracting routes from `main.py` into modular routers under `app/routes/`. It was created in response to **HOTFIX-20251001-001**, a production incident caused by incomplete route extraction.

**Key Principle:** **Gradual transition with parallel operation** until verified.

### Background

The FastAPI Window Quotation System originally had all routes in a 2,273-line `main.py`. During refactoring (TASK-001, TASK-002, TASK-003), routes were extracted to:
- `app/routes/auth.py` ✅ Successful
- `app/routes/quotes.py` ⚠️ Caused production incident
- `app/routes/materials.py` ✅ Successful
- `app/routes/work_orders.py` ✅ Successful

**The quotes router incident revealed critical gaps in our extraction process.**

### Core Philosophy

```
KEEP OLD → ADD NEW → TEST BOTH → VERIFY NEW → REMOVE OLD
     ↓          ↓          ↓           ↓            ↓
  Safe      Parallel   Redundancy  Confidence   Clean
```

**NOT:** ~~Remove old → Add new → Hope it works~~ ❌

---

## 2. When to Use This Protocol

### Required Situations

Use this protocol for:

✅ **Any route extraction from main.py to modular routers**
✅ **Refactoring routes that involve data processing**
✅ **Routes with template dependencies**
✅ **Routes with complex business logic**
✅ **High-traffic production endpoints**

### Optional Situations (Still Recommended)

Consider using for:
- New route creation (follow structure, skip extraction steps)
- Internal API endpoints (lower risk)
- Development-only routes

### When NOT to Use

Skip this protocol for:
- ❌ Static file routes
- ❌ Health check endpoints
- ❌ OpenAPI documentation routes

---
