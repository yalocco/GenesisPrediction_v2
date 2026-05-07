# GitHub Actions NoLLM Trial v7

Fix:
- `.env` is still generated for docker compose.
- Runtime secrets are also exported to `$GITHUB_ENV`.
- This lets normal Python scripts such as FX scripts read API keys via `os.getenv()`.

Required GitHub Secrets:
- NEWSAPI_KEY
- ALPHAVANTAGE_API_KEY

Optional GitHub Secret:
- EXCHANGERATE_HOST_ACCESS_KEY

After replacing the workflow file:
1. git add .
2. git commit -m "Export FX secrets for GitHub Actions runtime"
3. git push origin main
4. Re-run workflow from GitHub Actions UI
