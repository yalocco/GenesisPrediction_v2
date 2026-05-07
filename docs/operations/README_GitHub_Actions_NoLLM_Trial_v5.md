# GitHub Actions NoLLM Trial v5

Fix:
- Creates a minimal `.env` file inside the GitHub Actions runner.
- Reads `NEWSAPI_KEY` from GitHub Repository Secret.
- Keeps NoLLM mode as English-first and does not use Ollama.

Required GitHub Secret:
- NEWSAPI_KEY

After replacing the workflow file:
1. git add .
2. git commit -m "Add GitHub Actions minimal env for NoLLM trial"
3. git push origin main
4. Re-run workflow from GitHub Actions UI
