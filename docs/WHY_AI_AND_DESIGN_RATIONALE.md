# Why AI? — Design Rationale

This document captures the reasoning behind the computer-use automation system and the main design questions considered while building it.

It is supplementary documentation. The required project design write-up remains `REPORT.md`.

---

## 1. What problem are we solving?

Some legacy banking applications do not expose a usable API for performing business operations.

A human employee may need to:

1. Search for a member
2. Open the member profile
3. Open an account
4. Read or update information

The goal of this system is to make those UI-only workflows reusable by software agents.

---

## 2. Why not just let employees continue doing it manually?

Manual operation can be the right solution when:

- the task happens rarely,
- only a few workflows exist,
- or automation would cost more than the time saved.

Automation becomes more useful when the same tasks are repeated frequently across many users, institutions, or legacy applications.

The goal is not to replace employee knowledge. It is to capture repetitive workflows and execute them consistently.

---

## 3. Why not just write Playwright or Selenium scripts manually?

If the workflow is already known, manually written automation may be simpler.

The LLM becomes useful when the system knows the goal but does not yet know the exact UI workflow.

Example:

> Get the savings balance for member 100001.

The LLM can inspect the application, determine the required UI steps, and complete the workflow.

Once that workflow succeeds, it is saved as a reusable capability.

Future executions should not require the LLM to rediscover the same process.

---

## 4. What is the LLM actually doing?

During discovery:

**Goal → Observe UI → Decide next action → Act → Observe again**

The LLM acts as the reasoning layer.

The browser automation system acts as the execution layer.

Simple mental model:

**LLM finds the path. Automation repeats the path.**

---

## 5. Why deterministic replay?

Allowing an LLM to freely reason through the banking UI every time would introduce unnecessary:

- cost,
- latency,
- variability,
- and safety risk.

Instead:

**LLM discovery → saved capability → deterministic replay**

Once a workflow has been learned, the replay engine performs the known steps without an LLM deciding what to do next.

---

## 6. How does natural language fit into this?

A user or upstream agent may request:

> Show me the savings balance for member 100001.

If an approved capability already exists:

**Natural language → identify capability → deterministic replay → result**

If no capability exists yet:

**Natural language goal → discovery → successful workflow → new capability**

---

## 7. Should AI have access to every banking operation?

No.

Capabilities should be controlled according to risk.

Examples:

### Lower risk
- Search member
- Read balance
- View transaction history

### Higher risk
- Withdrawal
- Transfer
- Freeze account
- Close account

Higher-risk operations should be blocked or require explicit human approval.

The AI should never receive unrestricted control of the banking application.

---

## 8. Why did we build a legacy banking demo?

We do not have access to a real banking back-office system, and we should not attempt to obtain one.

The demo application gives us a controlled environment where we can demonstrate:

- member lookup,
- accounts,
- balances,
- transactions,
- deposits,
- withdrawals,
- transfers,
- permission errors,
- restricted accounts,
- slow responses,
- and other exceptional states.

The computer-use system is the actual project. The banking application is the test surface.

---

## 9. When would this architecture NOT make sense?

This architecture is not automatically better for every workflow.

If there are only a few stable workflows and they rarely change, manual operation or normal hand-written automation may be simpler.

The value increases when:

- many workflows exist,
- many legacy applications exist,
- workflows must be reused,
- and repeatedly hand-coding automation becomes expensive.

---

## 10. Core principle

> Use AI where reasoning and discovery are needed.  
> Use deterministic software where reliability and repeatability are needed.