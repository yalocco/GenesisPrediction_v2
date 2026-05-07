# GitHub Actions NoLLM Trial v6

Fix:
- Adds FX secrets to the generated `.env` file.
- Supports `ALPHAVANTAGE_API_KEY`.
- Supports `EXCHANGERATE_HOST_ACCESS_KEY` when present.
- Keeps NoLLM mode as English-first and does not use Ollama.

Required GitHub Secrets:
- NEWSAPI_KEY
- ALPHAVANTAGE_API_KEY

Optional GitHub Secret:
- EXCHANGERATE_HOST_ACCESS_KEY

After replacing the workflow file:
1. git add .
2. git commit -m "Add FX secrets to GitHub Actions NoLLM trial"
3. git push origin main
4. Re-run workflow from GitHub Actions UI
