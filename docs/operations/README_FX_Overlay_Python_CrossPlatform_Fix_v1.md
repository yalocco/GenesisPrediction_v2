# FX Overlay Python Cross-Platform Fix v1

Fix:
- Replaced Windows-only Python path:
  `.venv\Scripts\python.exe`
- Added cross-platform Python resolver:
  - Windows: `.venv/Scripts/python.exe`
  - Linux/GitHub Actions: `.venv/bin/python`
  - fallback: `python3`, then `python`
- Preserves previous TEMP cross-platform fix:
  `[System.IO.Path]::GetTempPath()`

Purpose:
- Keep home Windows Full/NoLLM operation intact.
- Allow GitHub Actions Ubuntu NoLLM trial to proceed past FX overlay sanitize phase.

Expected result:
- `Sanitize-DashboardCsv -PythonExe $PY` no longer receives null on GitHub Actions.
