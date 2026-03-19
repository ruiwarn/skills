# Architecture and Maintainability Review

Use this when the diff changes module boundaries, adds direct cross-module calls, introduces callback/event plumbing, reshapes state machines, or looks like one component is taking on too many responsibilities.

## First Questions

- Who owns the state?
- Is this interaction a command or a notification?
- Does the producer need to know the concrete consumer?
- If a second consumer is added, does the producer need to change?
- Are ordering, retries, or recovery encoded implicitly across modules?
- Is the caller reaching through layers it should not know about?

## Coupling Patterns to Flag

### 1. Hardcoded notification fan-out

Producer directly calls concrete consumers to announce something happened.

Common symptom:

```c
void nfc_on_tag_read(const tag_t *tag) {
    logger_on_tag(tag);
    ui_on_tag(tag);
    storage_on_tag(tag);
}
```

Why it matters:
- Producer owns every consumer
- Adding or removing listeners changes the producer
- Side effects become scattered and easy to miss in review

Prefer:
- Static observer list
- Callback registration
- Bounded RTOS queue or event flags
- Small publish/dispatch function with fixed-capacity listeners

Severity:
- `P1` if this sits on a safety-critical, recovery-critical, or cross-context path
- `P2` otherwise

### 2. Cross-layer reach-through

Application or service code manipulates driver/HAL internals directly, or a low layer calls back into a high layer without an explicit boundary.

Prefer:
- Narrow interface owned by one layer
- Adapter around legacy API
- Dependency inversion through an ops/interface struct

### 3. Bidirectional dependencies or split ownership

Two modules know too much about each other, or state is partially owned in both places.

Symptoms:
- Mutual includes or back-calls
- Shared flags updated in multiple layers
- One module must know another module's internal phases

Prefer:
- Single state owner
- Explicit mediator/orchestrator
- Event queue or callback boundary
- State machine with one owner

### 4. Temporal coupling

Correctness depends on callers knowing an undocumented order such as init, register, arm, enable, recover.

Prefer:
- Explicit state machine
- Single orchestration entry point
- Guarded transitions with clear preconditions

Raise severity when wrong ordering can drop events, deadlock recovery, or misconfigure hardware.

### 5. Mixed responsibilities

One function or module touches hardware, protocol parsing, retry policy, persistence, and user notification all at once.

Prefer:
- Split by reason to change
- Keep ISR/driver paths narrow
- Move policy decisions out of low-level code

### 6. Type branching spread across callers

Multiple call sites switch on mode, backend, or device type to decide behavior.

Prefer:
- Strategy or ops table
- State pattern when behavior follows lifecycle state
- Factory or compile-time wiring when construction is the only variable

### 7. Global singleton creep

Module pulls unrelated globals or singleton services instead of taking explicit dependencies.

Prefer:
- Explicit dependencies
- Static wiring in one composition point
- Small context struct

## Pattern Selection Hints

- Keep a direct call when there is one stable callee, synchronous semantics are required, and ownership is clear.
- Prefer observer or callback registration when the producer should not own consumers and the interaction is notification-like.
- Prefer an event queue or event flags when crossing ISR/task or asynchronous boundaries, as long as capacity and latency are bounded.
- Prefer a state machine when callers keep encoding phase ordering externally.
- Prefer strategy or interface structs when implementations vary behind one contract.
- Prefer adapter when cleaning up a legacy boundary.

Do not recommend heavyweight abstractions by default. In embedded code, the right answer is usually the smallest static mechanism that removes the concrete coupling.

## Embedded-Specific Guardrails

- Avoid recommending dynamic allocation unless the codebase already uses it safely.
- Prefer static registration, fixed-capacity tables, and bounded queues.
- Respect ISR restrictions, stack budgets, latency, and determinism.
- If a pattern increases hidden control flow more than it reduces coupling, it is the wrong pattern.

## Review Output Requirement

For every architecture finding, state:
- the concrete coupling symptom
- why it hurts: safety, sequencing, change amplification, portability, or testability
- the smallest viable alternative
- whether it should block now or can be follow-up work
