# AGENTS.md --- Instructions for AI Coding Agents

## 0. Project Directory Layout and Workflow

The repository is organized into three directories:

-   **`backend/`** — Python server application (FastAPI + SQLAlchemy). All backend code goes here.
-   **`frontend/`** — Client-side application (UI). All frontend work goes here.
-   **Planning docs** — AI agent planning and documentation (`TASK.md`, `PLAN.md`, this file, etc.) are located in the root directory.

**Workflow:**
1.  Read `PLAN.md` to identify the next uncompleted task item (under "Очередные задачи").
2.  Execute only that single task. Do not modify other parts of the plan.
3.  After completion, wait for user confirmation.
4.  Upon confirmation, move the completed task from "Очередные задачи" to "Выполненные" section in `PLAN.md`.
5.  Read the next uncompleted item and repeat.

Rules:
- Work on backend code in `backend/`.
- Work on frontend code in `frontend/`.
- Planning documentation is kept in the root directory.
- Do not create Git commits — user will handle them separately.
- Do not add new text or change numbering when moving tasks.
- **Do not create empty directory structures.** Create files and directories only when specific code needs to be written or concrete changes are being made. Skip creating boilerplate folders ahead of time; materialize the structure as part of actual implementation work.

## 1. Mission

## 2. Project Structure

The repository has three main root directories:

-   **`backend/`** — Server-side Python application (FastAPI + SQLAlchemy).
    This is where backend code belongs. All server implementation goes here.
-   **`frontend/`** — Client-side application (UI, API integration with the
    backend). All frontend work goes here.
-   **Planning docs** — AI agent planning and documentation. Contains:
        -   `TASK.md` — Functional requirements (detailed specifications)
        -   `AGENTS.md` — This file (instructions for AI coding agents)
        -   `PLAN.md` — Backend implementation plan
        -   Other planning/technical documents

**Work directory rules:**
- When working on backend code, use `backend/` as the working context.
- When working on frontend code, use `frontend/` as the working context.
- Planning documentation is kept in the root directory.

## 4. Operating with a local quantized model and a constrained context

Assume the coding agent may be a locally hosted, quantized model with
limited reasoning capacity, a limited context window, and/or context
(KV-cache) quantization. These constraints must shape the workflow.
Do not assume the model can reliably retain the entire repository,
conversation, or a long implementation plan in active context.

### Context-efficiency rules

- Work on one small, independently verifiable task at a time.
- Before editing, identify only the files and code paths relevant to the
  current task. Do not load the entire repository into the prompt.
- Read large files in focused sections. Search for symbols and inspect
  surrounding code instead of repeatedly printing whole files.
- Do not repeatedly reread `TASK.md`, `AGENTS.md`, or files already
  summarized in the current task checkpoint. Reopen the source only
  when a specific detail needs verification.
- Keep tool output compact: request relevant lines, concise diffs, and
  test summaries. Avoid dumping dependency trees, generated files,
  lockfiles, minified assets, or large logs into the context.
- Never ask the model to implement several unrelated modules in one
  prompt. Split work into small steps with explicit inputs and expected
  outputs.
- Avoid unnecessary speculation and long explanations. Prefer concise
  plans, decisions, and reports backed by repository evidence.
- Do not omit important requirements merely to save tokens. Preserve
  critical business rules, API constraints, security requirements, and
  unresolved questions in durable project notes.

### Progress tracking and recovery

Use `PLAN.md` as the source of truth for backend development progress. The plan contains two sections:
- **Выполненные** — completed tasks (read to confirm what was done)
- **Очередные задачи** — remaining tasks in order (pick one to execute)

When working on a task:
1.  Read only the relevant section from `PLAN.md` to understand context.
2.  After completing the current item, wait for user confirmation.
3.  Upon confirmation, move that item to the **Выполненные** section without changing numbering or adding new text.
4.  Pick the next uncompleted item and continue.

Do not use `PLAN.md` as a replacement for source code, tests, API documentation, or `TASK.md`. It is a progress tracker, not technical documentation.

### Prompt and response discipline

For each implementation step, formulate a compact work unit containing:

- Goal.
- Relevant files / symbols.
- Constraints that must not be violated.
- Expected change.
- Exact verification command(s).

After completing it, report only:

- What changed.
- Files affected.
- Checks run and results.
- Remaining risk or blocker.
- Next step.

If the context limit is reached, stop safely after saving progress.
Do not continue from uncertain or partially remembered state.

### Reliability safeguards for quantized models

- Treat generated code and conclusions as unverified until inspected
  and tested.
- Do not make broad edits based on a vague understanding of the code.
- For consequential behavior (Keitaro flow routing, offer calculations,
  campaign mutations, authentication, and secret handling), locate the
  authoritative implementation or documentation and verify the result
  with focused tests.
- Prefer explicit types, small functions, clear names, and simple
  control flow over clever abstractions or compressed code.
- Avoid unnecessary dependencies, framework changes, and large
  refactors.
- When uncertain, state what is unknown and ask one focused question
  rather than filling gaps with a plausible guess.
- Review every diff for accidental deletions, duplicated logic,
  fabricated API fields, and changes outside the current work unit.

## 6. Source of truth and ambiguity handling

Before changing files:

1.  Read `TASK.md` completely.
2.  Inspect the repository structure, README, dependency manifests,
    configuration, existing source code, and tests.
3.  Identify the current language, framework, runtime, package manager,
    test runner, formatting and linting tools.
4.  Find existing API clients, domain models, configuration patterns,
    and UI conventions.
5.  Inspect Git status. Do not overwrite or discard pre-existing user
    changes.
6.  Identify the Keitaro API version and the available documentation or
    API schema.
7.  Watch the editor reference video from `TASK.md` before implementing
    offer-editing calculations.

Do not assume a framework, directory layout, endpoint, request schema,
or business rule before checking the repository and source material.

If the video or API documentation is unavailable, do not invent the
missing behavior. Continue with independent work where possible and
record the blocker and the exact unanswered questions.

## 7. Planning and execution

Work in small, reviewable steps.

Use `PLAN.md` to track backend progress between sessions and model-context resets.

Before implementation, create or present a concise plan containing:

-   Relevant files and modules.
-   API operations required.
-   Data flow from UI to Keitaro and back.
-   Validation and error-handling approach.
-   Test strategy.
-   Known uncertainties and dependencies.

Implement one coherent step at a time. After each step:

1.  Run the narrowest relevant tests or checks.
2.  Inspect the diff.
3.  Fix regressions before moving on.
4.  Update project documentation or progress notes when the architecture
    or behavior changes.

Do not perform broad unrelated refactors. Preserve existing project
conventions unless they directly prevent correct implementation.

## 8. Architecture and separation of concerns

Follow the architecture already used by the repository. Regardless of
framework, maintain clear boundaries between:

-   Presentation/UI.
-   Application or use-case logic.
-   Keitaro API integration.
-   Domain validation and business rules.
-   Configuration and secrets.
-   Tests.

Specific rules:

-   UI components must not contain raw Keitaro HTTP request logic.
-   Keep API communication behind a dedicated client/service or the
    project's established equivalent.
-   Keep offer calculation and campaign-configuration rules in testable
    application/domain code, not scattered across UI handlers.
-   Validate user input before making external API calls.
-   Treat API responses as untrusted external data and validate the
    fields needed by the application.
-   Avoid duplicate API request construction and duplicate error
    mapping.
-   Use the project's established typing, DTO, schema, and naming
    conventions.

Do not introduce a new architectural framework or dependency unless
there is a concrete need.

## 9. Keitaro API integration

Before implementing an operation, verify its endpoint, method,
authentication, required fields, response shape, and side effects
against the target API documentation or a safe test request.

The integration layer must:

-   Centralize base URL and authentication configuration.
-   Apply explicit connection/read timeouts using the conventions of the
    current HTTP library.
-   Handle non-success HTTP statuses.
-   Distinguish transport failures, authentication/authorization
    failures, validation failures, and API business errors where
    possible.
-   Avoid logging credentials, authorization headers, or sensitive
    campaign data.
-   Validate and normalize API responses at the boundary.
-   Avoid unsafe automatic retries for non-idempotent operations.
-   Expose useful, sanitized errors to application code.

Do not expose the Keitaro API token to browser/client code. All
authenticated Keitaro requests must execute in a trusted server-side
environment.

### Multi-step campaign creation

Campaign creation may require several API calls. Treat it as a
multi-step operation:

1.  Validate all user-supplied and configured identifiers.
2.  Verify referenced entities when the API supports safe lookup.
3.  Create the campaign.
4.  Configure its required domain, group, and traffic source.
5.  Create/configure both required flows.
6.  Verify the resulting campaign state if the API supports retrieval.

Do not report complete success until all required steps have succeeded.

If a later step fails after earlier steps have succeeded:

-   Preserve the error details needed for diagnosis without exposing
    secrets.
-   Report partial completion accurately.
-   Use compensating deletion/rollback only when the API supports it and
    the action is safe.
-   Never silently leave the user believing the campaign is fully
    configured.

### Flow requirements

The created campaign must have exactly the intended two-flow behavior
described in `TASK.md`:

-   One flow matches the specified country and redirects matching
    traffic to Google.
-   The other flow redirects to the selected Keitaro offer.

Verify how Keitaro evaluates flow order, conditions, and fallback
behavior before configuring them. Do not assume that the order in which
flows are created determines execution priority.

## 10. Offer editor and numeric correctness

The offer editor is a business-critical area.

Before implementing calculations:

1.  Watch the complete reference video.
2.  Record the initial state and each user action.
3.  Record every displayed numeric field before and after each action.
4.  Determine the exact formula and rounding behavior from the
    demonstrated behavior and API data.
5.  Check edge cases, including adding an existing offer, removing an
    absent offer, and removing the final offer.
6.  Confirm which values are persisted by Keitaro and which are derived
    for display.

Rules:

-   Do not guess the meaning of numeric fields.
-   Do not use arbitrary equal distribution or percentage normalization
    unless the reference behavior/API confirms it.
-   Avoid floating-point drift for percentages or decimal values; use
    the project's appropriate decimal/integer representation.
-   Make calculations deterministic and independently unit-testable.
-   Ensure the UI displays values derived from the authoritative server
    state or from a verified deterministic rule.
-   After a successful mutation, refresh or otherwise reconcile with the
    server response.
-   After a failed mutation, do not leave optimistic UI state presented
    as saved.

If the reference video cannot be accessed, stop short of implementing
unverified calculation behavior and report the missing evidence.

## 11. Validation and user experience

-   Validate required fields and formats on the server boundary, even if
    the UI also validates them.
-   Display actionable, sanitized error messages.
-   Show loading/pending states for network operations.
-   Prevent accidental duplicate submissions while an operation is
    pending.
-   Confirm destructive operations where appropriate.
-   Disable actions that are invalid for the current state.
-   Do not display success until the server confirms the operation.
-   Keep the visible campaign and offer data synchronized with Keitaro.
-   Do not use hardcoded fake data in production paths. Mocks are
    allowed in tests and explicitly designated development/demo modes.

## 12. Security and configuration

-   Read credentials from environment variables or the repository's
    established secret-management mechanism.
-   Never commit real API tokens, passwords, or private URLs.
-   Never put the Keitaro token in frontend code, browser storage,
    public runtime configuration, or client-visible responses.
-   Add/update an example environment file with placeholder values only,
    if appropriate.
-   Ensure example files are excluded from secret scanning only when
    they contain placeholders, not real credentials.
-   Sanitize logs and exceptions.
-   Do not weaken authentication, CORS, or access controls to make local
    development easier.

## 13. Testing requirements

Use the existing test framework and conventions.

At minimum, cover:

### Campaign creation

-   Required-field validation.
-   Invalid country code and offer identifier handling.
-   Correct API payload construction.
-   Campaign configuration with domain, group, and traffic source.
-   Creation of both flows with the required matching and redirect
    behavior.
-   API authentication and transport errors.
-   Partial failure during multi-step creation.

### Offer editor

-   Loading campaign offers.
-   Adding an offer.
-   Removing an offer.
-   Duplicate/missing offer handling according to verified business
    rules.
-   Numeric calculations and rounding based on the reference behavior.
-   Edge cases, including an empty offer list if allowed.
-   Reconciliation after successful API mutation.
-   State handling after failed API mutation.

### General

-   Credentials are not exposed to client code or logs.
-   No success response is returned for a failed operation.
-   Existing tests continue to pass.

Mock external HTTP calls in unit tests. Use a real Keitaro instance only
for explicitly configured integration tests against a safe test
environment. Never run destructive tests against production campaigns.

## 14. Code quality

-   Follow existing style and naming conventions.
-   Prefer small, cohesive functions and modules.
-   Add types and schemas consistent with the repository.
-   Avoid unnecessary abstractions and speculative generalization.
-   Handle exceptions at meaningful boundaries; do not swallow
    exceptions.
-   Do not use broad catch-all handling that converts every failure into
    success-shaped output.
-   Keep comments focused on non-obvious business rules and API quirks.
-   Do not add dependencies when the standard library or existing
    project dependencies are sufficient.
-   Do not change public interfaces without checking all call sites.
-   **Never use imports inside functions and classes; place them only at the top of the file.**
    Imports that are needed only for type hints must be placed under `from __future__ import annotations` or guarded with `if TYPE_CHECKING`.

## 15. Documentation

Update README or the existing project documentation with:

-   Prerequisites.
-   Installation/setup steps.
-   Required environment variables.
-   How to run the application.
-   How to run tests and quality checks.
-   How to configure the Keitaro API connection.
-   Any verified limitations or assumptions.

Document API-specific decisions and offer-calculation rules close to the
implementation or in a dedicated technical note.

Never document an unverified assumption as an established fact.

## 16. Completion checklist

Before declaring the task complete, verify:

-   [ ] `TASK.md` requirements have been reviewed.
-   [ ] Existing repository conventions have been followed.
-   [ ] Keitaro API contracts have been verified.
-   [ ] Campaign creation creates the required campaign configuration
    and two flows.
-   [ ] Country matching and both redirect destinations are correct.
-   [ ] Domain, group, and traffic source are configured correctly.
-   [ ] Existing campaigns can be loaded.
-   [ ] Offers can be added and removed.
-   [ ] Numeric behavior matches the reference video and API contract.
-   [ ] UI state is reconciled with server state.
-   [ ] Partial failures and API errors are handled safely.
-   [ ] Credentials remain server-side and are not logged.
-   [ ] Relevant automated tests pass.
-   [ ] Existing tests and unrelated functionality remain intact.
-   [ ] Setup and usage documentation is current.
-   [ ] The final diff contains no unrelated changes.


When finishing a work session, report:

1.  **Implemented:** concrete behavior and files changed.
2.  **Verification:** tests/checks run and their results.
3.  **API integration:** operations verified against Keitaro, and any
    mocks used.
4.  **Open questions/blockers:** unresolved requirements or unavailable
    resources.
5.  **Next steps:** the smallest useful next implementation step.

Do not claim that an operation was tested against Keitaro if it was only
tested with mocks.

## 17. Final report format
