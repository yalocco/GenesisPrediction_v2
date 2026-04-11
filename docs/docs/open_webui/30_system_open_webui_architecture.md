## Core Architecture (Genesis Model)

scripts layer (Python)
- Responsible for all computation, data processing, and generation
- Executes via Morning Ritual or batch processes
- Produces analysis artifacts (JSON)

analysis layer (SST)
- Stores generated artifacts from scripts
- Single Source of Truth
- Used by all upper layers
- No computation occurs here

UI layer (open-webui / static UI)
- Read-only layer
- Displays data from analysis only
- Never performs calculation or logic generation