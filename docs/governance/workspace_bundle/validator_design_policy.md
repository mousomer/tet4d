# Validator Design Policy

Structural errors should fail.

Suspicious findings should default to advisory unless strict mode is enabled.

Strict mode should be opt-in through an environment variable or explicit command
flag.

Suppressions must be local, narrow, and reasoned.

Validators should use deterministic traversal and stable output.

Validators should avoid external dependencies unless the project explicitly
requires them.

Validator output should be concise and actionable.
