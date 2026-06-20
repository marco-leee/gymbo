<!--
Sync Impact Report
==================
Version change: (uninitialized template) → 1.0.0
Modified principles: N/A (initial ratification)
Added sections:
  - Core Principles (9 principles from user input)
  - Additional Constraints (ADHD-aware design, tech stack)
  - Development Workflow (feature dirs, change logging, chores)
  - Governance
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ updated
  - .specify/templates/tasks-template.md ✅ updated
  - .specify/templates/commands/*.md ⚠ N/A (no command files present)
  - PRINCIPLES.md ⚠ pending (existing file; constitution is authoritative source)
  - AGENTS.md ⚠ pending (references PRINCIPLES.md; no change required)
Follow-up TODOs: None
-->

# Gymbo Constitution

## Core Principles

### I. Principle Awareness

All agents MUST apply every principle in this constitution to all actions and
decisions. No principle may be ignored because another task appears more urgent.

**Rationale**: Consistent behavior across agents and sessions depends on
explicit, recurring adherence—not selective application.

### II. Follow Instructions

Agents MUST follow the instructions provided to them. They MUST NOT invent
substitute instructions, workflows, or requirements.

**Rationale**: Unauthorized improvisation causes drift from project intent and
makes outcomes unpredictable for developers.

### III. No Assumptions

Agents MUST NOT make assumptions when instructions are incomplete or ambiguous.
They MUST ask for clarification before proceeding.

**Rationale**: Assumptions produce rework. Clarification upfront is cheaper
than correcting wrong implementations.

### IV. KISS (Keep It Simple, Stupid)

Actions and decisions MUST be simple and straightforward. Complexity MUST be
justified before adoption.

**Rationale**: Simple solutions are easier to review, maintain, and reason
about—especially for developers with ADHD traits.

### V. DRY (Don't Repeat Yourself)

Code MUST be reusable. Duplicated logic MUST be extracted into shared
functions, modules, or components rather than copied.

**Rationale**: A single source of truth reduces bugs and maintenance cost.

### VI. YAGNI (You Aren't Gonna Need It)

Features MUST only be built when users actually need them. Speculative or
"might need later" functionality is prohibited unless explicitly requested.

**Rationale**: Unused code adds cognitive load and maintenance burden without
delivering value.

### VII. Modularize

Components MUST be broken into smaller, reusable parts with clear boundaries
and single responsibilities.

**Rationale**: Modular design supports DRY, simplifies testing, and enables
incremental delivery.

### VIII. Visual Communication

When communicating with developers, agents MUST use visual aids where they aid
understanding. Mermaid diagrams are the preferred format for architecture,
flows, and relationships.

**Rationale**: Visual representations reduce cognitive load and make complex
systems faster to grasp.

### IX. Change Logging

When performing a task, agents MUST document what changed. They MUST locate the
correct log file in the feature directory (e.g., `doc/features/<feature>/log.md`)
and append a change record. For chores without a feature folder, record plans in
`doc/plans/` and execution in `doc/tasks/`.

**Rationale**: Persistent change logs create an auditable history and help
developers track feature evolution without reconstructing context from diffs
alone.

## Additional Constraints

### ADHD-Aware Design

UI/UX decisions MUST consider users with ADHD traits. Interfaces MUST minimize
cognitive load: minimalistic layout, clear hierarchy, supportive language, and
no unnecessary information density.

**Rationale**: Gymbo serves people with ADHD traits; overwhelming interfaces
directly undermine the product's purpose.

### Technology & Architecture

- Frontend MUST use SvelteKit and TailwindCSS with `bun` as package manager.
- Architecture MUST follow [ARCHITECTURE.md](../../ARCHITECTURE.md). Deviations
  require explicit approval documented in the relevant feature plan.
- Runtime agent guidance in [AGENTS.md](../../AGENTS.md) and
  [PRINCIPLES.md](../../PRINCIPLES.md) supplements this constitution but does
  not override it.

## Development Workflow

### Feature Development

1. Copy the template from `doc/features/template/` into a new hyphen-separated
   feature directory (e.g., `doc/features/my-new-feature/`).
2. Fill in `requirements.md`, `plan.md`, `changes.md`, and `log.md`.
3. Run Constitution Check (see plan template) before Phase 0 research.
4. Append all task completions to the feature `log.md` per Principle IX.

### Constitution Check Gate

Every implementation plan MUST include a Constitution Check section that
verifies compliance with all nine core principles before work begins. Violations
requiring exceptions MUST be documented in the plan's Complexity Tracking table
with justification.

### Chores Without Feature Folders

Tasks that do not belong to a feature directory MUST record plans in
`doc/plans/` and execution notes in `doc/tasks/`.

## Governance

This constitution supersedes conflicting practices across specs, plans, tasks,
and agent guidance unless an explicit, documented exception is approved.

**Amendment procedure**:

1. Propose changes via `/speckit-constitution` with rationale.
2. Bump version per semantic rules below.
3. Propagate updates to dependent templates and guidance files.
4. Record the amendment date.

**Versioning policy**:

- **MAJOR**: Backward-incompatible principle removals or redefinitions.
- **MINOR**: New principles or materially expanded guidance.
- **PATCH**: Clarifications, wording fixes, non-semantic refinements.

**Compliance review**: All specs, plans, and task lists MUST verify compliance
with this constitution. PRs and agent work MUST pass Constitution Check gates.
Unjustified complexity MUST be rejected or documented in Complexity Tracking.

**Version**: 1.0.0 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-06-20
