# FX Rates Sleep Fix v1

Purpose:
- Avoid AlphaVantage free-tier API rate limiting on GitHub Actions.

Change:
- Added:
  Start-Sleep -Seconds 2
- Inserted between usdthb and usdjpy requests.

Expected:
- GitHub Actions NoLLM workflow should proceed past FX rates stage.
