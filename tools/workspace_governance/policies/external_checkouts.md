# External checkout governance

Owner: the workspace policy owner. This policy supplies the preservation mode
for the all-repository rollout authorized by the workspace owner. A private
registry binds each observed location, classification, owner, reason and release
identity. An inventory proposal alone does not establish this binding.

All locations retain the shared safety and evidence principles. Direct project
adoption installs bounded dispatch and actual runner checks. The following
locations use central read-only governance during this rollout:

- Existing worktrees retain their branch, local changes and adopted project
  authority. Inspect them individually; changing a primary checkout does not
  prove another worktree's installation or product acceptance.
- Reference and learning checkouts retain upstream product authority. Treat
  their code as reference material until a task establishes direct maintenance.
- Dependencies, submodules, extensions and package caches retain their owning
  package or parent workflow. Do not rewrite package internals to add governance.
- Experiment outputs and backups retain producing-project or archival ownership.
  Preserve their bytes, inputs and provenance; inspect producing workflows when
  a task changes their generation or acceptance.
- Application-owned Git stores and repository metadata retain their application
  owner. Preserve administrative data and inspect through the owning application
  or repository rather than treating the store as a product checkout.

Read-only governance certifies a preservation instruction and its observed
location. It does not establish installed files, product correctness, an
exception to stronger rules, or verification of the producing workflow. Keep
missing owners, unresolved Git roots and unavailable inputs blocked. A future
maintenance task can establish direct bindings under its actual authorization
and accepted authority; it must preserve the applicable stronger obligations.
