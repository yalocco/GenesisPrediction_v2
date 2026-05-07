# TEMP Cross-Platform Fix v1

Fix:
- Replaced Windows-only `$env:TEMP`
- Uses `[System.IO.Path]::GetTempPath()` instead

Purpose:
- Linux / GitHub Actions compatibility
- Keeps Windows compatibility intact

Expected result:
- GitHub Actions NoLLM trial proceeds past summary materializer phase.
