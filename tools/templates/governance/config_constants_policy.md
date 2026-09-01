# Config and Constants Policy

Status: NON-AUTHORITATIVE TEMPLATE; project-bootstrap only; not tet4d governance.

Nontrivial constants belong in the adopting project's standard config/constants
authority.

Allowed trivial literals typically include:

- `0`
- `1`
- `-1`
- booleans/nulls
- empty string
- local loop/index literals
- file extensions and version strings when local and obvious

Generated config reference files are outputs, not source authority.
