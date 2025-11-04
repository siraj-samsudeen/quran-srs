# Start Wallaby for E2E tests
{:ok, _} = Application.ensure_all_started(:wallaby)

ExUnit.start()
Ecto.Adapters.SQL.Sandbox.mode(QuranSrs.Repo, :manual)
