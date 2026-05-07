# GitHub Actions run_daily_with_publish Linux Fix v1

Purpose:
- Allow the existing Morning Ritual / NoLLM workflow to continue on GitHub Actions Ubuntu runners.

Changes:
- Resolve Python cross-platform:
  - Windows .venv/Scripts/python.exe
  - Linux .venv/bin/python
  - system python3/python fallback
- Repair Docker-created data file ownership after analyzer runs on Linux.
- Keep Windows behavior intact for home PC Full mode.
- Make embedded Python materializer paths platform-neutral.

Why:
- GitHub Actions reached the analyzer phase successfully.
- The failure was caused by Docker-created files being owned by root on Linux.
- PowerShell outside Docker could not copy the raw news JSON.

Expected behavior:
- Home Windows Full mode remains supported.
- Home Windows NoLLM mode remains supported.
- GitHub Actions NoLLM trial can proceed past analyzer materialization.
