# FX Overlay TEMP Cross-Platform Fix v1

Fix:
- Replaced Windows-only `$env:TEMP` usage
- Uses `[System.IO.Path]::GetTempPath()` instead

Purpose:
- Linux / GitHub Actions compatibility
- Keeps Windows compatibility intact

Expected result:
- GitHub Actions NoLLM trial proceeds past FX overlay sanitize phase.
