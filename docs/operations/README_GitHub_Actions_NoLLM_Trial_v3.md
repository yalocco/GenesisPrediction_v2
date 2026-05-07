# GitHub Actions NoLLM Trial v3

Fix:
- Correct PowerShell argument passing for -Date and -NoLLM
- Previous workflow passed arguments as a malformed string
- This version uses multiline PowerShell invocation

After replacing the workflow file:
1. git add .
2. git commit -m "Fix GitHub Actions PowerShell argument passing"
3. git push origin main
4. Re-run workflow from GitHub Actions UI
