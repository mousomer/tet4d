# Secrets Policy

No secrets may be committed or included in prompts, logs, traces, screenshots,
docs, tests, config, or exported bundles.

Forbidden:

- API keys
- tokens
- passwords
- private keys
- signing credentials
- private URLs
- local absolute paths containing usernames
- production credentials
- `.env` contents

Allowed:

- `.env.example` with fake placeholder values
- documented environment variable names without real values
- redacted logs

If a secret is found, stop and report it. Do not copy it into another file.
