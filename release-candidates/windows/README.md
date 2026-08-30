# Windows Design Laboratory test candidate

This directory records how to retrieve validator-approved Windows packages
without committing generated binaries to normal Git history. The nominated
0.7.5 package was:

```text
Tet4D-Designer-0.7.5-windows-x86_64.zip
SHA-256 04941cb3f6d1070521f7a4d2d306fee5478908e3cf5e51d782c96a7e973913b9
Size 39,320,138 bytes
```

Retrieve the ZIP from the originating GitHub Actions run or release-candidate
asset storage, verify the checksum, extract it to a user-writable directory,
and launch
`Tet4D Designer/Tet4DDesigner.exe`. Python and the Godot editor are not
required.

That package passed repository, ZIP inventory, PE header, embedded resource,
version, and path-sanitation validation. Direct clean-machine Windows launch
and human Design Laboratory acceptance remain pending; the presence of this
candidate is distribution evidence, not runtime-acceptance evidence.

Generated packaging output remains ignored under `artifacts/godot/`. ZIPs must
remain outside Git and be exchanged through Actions artifacts, release assets,
or canonical release-candidate asset storage. This directory intentionally
contains metadata only.
