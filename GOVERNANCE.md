# Governance Model

This document outlines the governance and decision-making model of Orix X.

---

## Core Roles

### 1. Maintainers / Core Team
Maintainers have write access to the main codebase. They are responsible for reviewing pull requests, managing releases, establishing long-term product vision, and enforcing the Code of Conduct.

### 2. Contributors
Contributors are community members who submit code, tests, documentation, or template updates. To become a maintainer, a contributor must demonstrate consistent technical excellence, alignment with Orix X's open-source values, and active community participation.

### 3. SteerCo (Steering Committee)
A small panel composed of key architects from Kryonara and top open-source contributors. The Steering Committee resolves architectural disagreements and guides major technical shifts (e.g. moving from python-based local rendering to a WebAssembly/Go plugin model).

---

## Decision-Making Process

We follow a consensus-seeking model:
- **Minor Changes**: Resolved via standard pull request review with approval from at least one core maintainer.
- **Major Features (Orix RFCs)**: Require a formal RFC issue detailing proposed API changes, performance impacts, and design patterns. The RFC remains open for comments for 7 days, after which it requires a simple majority approval from the Core Team.
