# Windows Design Laboratory test candidate

This directory contains the exact validator-approved Windows package nominated
for clean-machine testing from branch `codex/built-in-style-catalog`:

```text
Tet4D-Designer-0.7.5-windows-x86_64.zip
SHA-256 04941cb3f6d1070521f7a4d2d306fee5478908e3cf5e51d782c96a7e973913b9
Size 39,320,138 bytes
```

Retrieve the branch on the Windows machine, verify the checksum, extract the
ZIP to a user-writable directory, and launch
`Tet4D Designer/Tet4DDesigner.exe`. Python and the Godot editor are not
required.

The package has passed repository, ZIP inventory, PE header, embedded resource,
version, and path-sanitation validation. Direct clean-machine Windows launch
and human Design Laboratory acceptance remain pending; the presence of this
tracked candidate is distribution evidence, not runtime-acceptance evidence.

Generated packaging output remains ignored under `artifacts/godot/`. Only the
exact nominated candidate is tracked here.
