# AgentConfig

**The open agent format for Apple platforms.**

AgentConfig is a portable, snake_case JSON manifest that fully describes an
AI agent — prompt, model strategy, runtime limits, memory, retrieval, tools,
and guardrails — in a single document you can check into source control, ship
inside an app bundle, or serve from a control plane. The same manifest that
drives a server-side runtime can drive an on-device runtime built on Apple's
Foundation Models framework: the format says *what* the agent is, never
*where* it runs.

```json
{
  "id": "story_companion",
  "name": "Story Companion",
  "version": "v1",
  "schema_version": "2",
  "system_prompt": "You are a friendly bedtime-story companion.",
  "runtime": { "streaming": true, "max_turns": 6 },
  "model": {
    "strategy": "fallback",
    "candidates": [
      { "name": "on_device", "model": "apple:foundation-models" },
      { "name": "cloud", "model": "anthropic:claude-haiku-4-5" }
    ]
  }
}
```

Complete examples live in [`examples/`](examples/); the formal contract is
the JSON Schema at
[`schema/agent-config.v2.schema.json`](schema/agent-config.v2.schema.json).

## Design principles

- **One artifact, any runtime.** A manifest is a plain JSON document. Nothing
  in it names a server, a tenant, or a deployment. Once a manifest exists
  locally, executing it requires no control plane.
- **Secrets never ship in the artifact.** Model candidates reference
  providers (`"openai:gpt-4o"`, `"apple:foundation-models"`); API keys are
  supplied by the runtime from its own environment, request, or keychain.
  A manifest is always safe to commit and to publish.
- **Pass-through by default.** Validators accept unknown members and tools
  preserve them (see [VERSIONING.md](VERSIONING.md)). A retrieval-capable
  cloud runtime and a minimal on-device runtime can consume the same
  manifest; each ignores what it doesn't implement without destroying it.
- **Versioned contract.** `schema_version` gates execution. Breaking changes
  get a new schema version and a new schema file; additive optional fields
  don't.

## Manifest reference

Top-level required fields: `id`, `name`, `version`, `schema_version`,
`system_prompt`, `runtime`, `model`. Everything else is optional.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable agent identifier (slug). |
| `name` | string | Human-readable name. |
| `version` | string | Author-owned config version label (e.g. `"v2"`). |
| `schema_version` | string | Manifest schema version. Currently `"2"`. |
| `system_prompt` | string | The agent's system prompt. |
| `description` | string? | Optional description. |
| `tags` | [string]? | Optional free-form tags. |

### `runtime` — execution limits *(required)*

| Field | Type | Meaning |
|---|---|---|
| `streaming` | bool | Whether responses stream. |
| `max_turns` | int? | Max agent-loop turns per request. |
| `max_concurrent_tools` | int? | Max tool calls in flight at once. |

### `model` — model strategy and candidates *(required)*

| Field | Type | Meaning |
|---|---|---|
| `strategy` | string | How the runtime picks a candidate: `"single"`, `"weighted"`, `"fallback"`, or a runtime-defined strategy. |
| `candidates` | [candidate] | Models the strategy selects from. Each has a `name` (unique in the manifest) and a `model` in `"provider:model"` form. |
| `routing_policy` | object? | Strategy-specific options (e.g. `{"sticky": true}`, `{"prefer_on_device": true}`). Pass-through for the runtime. |

The `provider:` prefix is how one manifest spans on-device and cloud:
`apple:foundation-models` runs locally, `anthropic:…`/`openai:…` run against
an API the runtime holds keys for.

### `memory` — conversation memory

| Field | Type | Meaning |
|---|---|---|
| `type` | string? | Memory implementation (e.g. `"buffer"`). |
| `window_turns` | int? | Turns retained in the window. |

### `retrieval` — RAG settings

| Field | Type | Meaning |
|---|---|---|
| `enabled` | bool | Whether retrieval is active *(required if section present)*. |
| `corpus_ids` | [string]? | Corpora to search (runtime-defined identifiers). |
| `top_k` | int? | Documents to retrieve. |
| `rerank` | bool? | Whether to rerank results. |
| `filters` | object? | Arbitrary retrieval filters; pass-through. |

### `tools` — tool surface

| Field | Type | Meaning |
|---|---|---|
| `allowed` | [string]? | Ordered allow-list of tool names. **Absent** means no allow-list is declared; **`[]`** is an explicit allow-list enabling no tools. |
| `definitions` | [tool]? | Tool schemas: `name`, `description`, JSON-Schema `parameters`, and an optional HTTP `endpoint` (`url`, `method` defaulting to `POST`, static `headers`). Tools without an endpoint are executed natively by the runtime or host app. |
| `tool_policy` | object? | Cross-tool constraints: `require_user_confirmation` (tool names needing explicit user approval), `max_total_runtime_ms`, `max_tools_per_turn`. |

A manifest may carry `definitions` without `allowed`; consumers apply their
own normalization rather than inferring hidden built-in tools.

### `guardrails` — safety switches

| Field | Type | Meaning |
|---|---|---|
| `pii_redaction` | bool? | Redact PII. |
| `jailbreak_detection` | bool? | Screen for jailbreak attempts. |
| `blocked_topics` | [string]? | Topics the agent refuses. |

Guardrail semantics are runtime-defined; unknown members are pass-through.

## Validating a manifest

```sh
pip install jsonschema
python scripts/validate.py
```

CI runs the same script on every push: all manifests in `examples/` must
validate and every manifest in `examples/invalid/` must be rejected.

To validate your own manifest:

```sh
python -c "
import json, sys
from jsonschema import Draft202012Validator
schema = json.load(open('schema/agent-config.v2.schema.json'))
Draft202012Validator(schema).validate(json.load(open(sys.argv[1])))
print('valid')
" path/to/your-agent.json
```

## Who uses this

- [AgentFactory](https://github.com/InfinitIQ-Tech) — Swift Vapor control
  plane that publishes versioned agent configs and exports this artifact.
  Contract-drift CI keeps its wire format and this schema in lockstep.
- [AgentFactoryDTO](https://github.com/InfinitIQ-Tech/AgentFactoryDTO) —
  Swift `Codable` models for the manifest.
- A Swift on-device agent runtime for Apple's Foundation Models framework is
  in development and consumes these manifests directly.

## License

[MIT](LICENSE)
