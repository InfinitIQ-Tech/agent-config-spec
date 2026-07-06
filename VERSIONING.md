# Schema versioning policy

Every AgentConfig manifest carries a `schema_version` string. It names the
contract the manifest was written against, and it is how runtimes decide
whether they can execute a manifest at all.

## Rules

1. **`schema_version` is a string integer** (`"2"`, `"3"`, …). It versions the
   *schema*, not the agent — the agent's own `version` field is free-form and
   author-owned.
2. **Breaking changes bump `schema_version`.** Removing a field, renaming a
   field, changing a type, or adding a new *required* field is breaking. Each
   schema version is published as its own file
   (`schema/agent-config.v2.schema.json`, `schema/agent-config.v3.schema.json`, …)
   and old versions are never edited except for documentation fixes.
3. **Additive optional fields do not bump `schema_version`.** New optional
   members may appear within a schema version. This only works because of the
   pass-through rule below.
4. **Pass-through rule.** Validators MUST accept members they do not
   recognize, and tooling (loaders, CLIs, packagers, control planes) MUST
   preserve them rather than dropping them. A manifest that round-trips
   through any conforming tool is byte-equivalent in content, unknown
   sections included. Fields a specific runtime does not support remain in
   the artifact as pass-through metadata.
5. **Runtimes declare what they execute.** A runtime that sees an unknown
   `schema_version` must refuse to run the manifest rather than guess. A
   runtime that sees unknown *members* under a known `schema_version` runs
   the manifest and ignores (but preserves) what it doesn't understand.
6. **Secrets are never part of any schema version.** Provider API keys and
   other credentials are supplied at runtime and MUST NOT appear in a
   manifest. Schema changes that would embed credentials will be rejected.

## Current version

The current schema version is **2**, defined by
[`schema/agent-config.v2.schema.json`](schema/agent-config.v2.schema.json).
