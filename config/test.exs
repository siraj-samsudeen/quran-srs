import Config

# Only in tests, remove the complexity from the password hashing algorithm
config :bcrypt_elixir, :log_rounds, 1

# Configure your database
#
# The MIX_TEST_PARTITION environment variable can be used
# to provide built-in test partitioning in CI environment.
# Run `mix help test` for more information.
config :quran_srs, QuranSrs.Repo,
  username: "postgres",
  password: "postgres",
  hostname: "localhost",
  database: "quran_srs_test#{System.get_env("MIX_TEST_PARTITION")}",
  pool: Ecto.Adapters.SQL.Sandbox,
  pool_size: System.schedulers_online() * 2

# We don't run a server during test. If one is required,
# you can enable the server option below.
config :quran_srs, QuranSrsWeb.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: 4002],
  secret_key_base: "fDHemjP4fFgvna7Zxf1w90J858fTWxxCtU1qn27wBxk2xGjgOLOlNCtU3NgIMono",
  server: false

# In test we don't send emails
config :quran_srs, QuranSrs.Mailer, adapter: Swoosh.Adapters.Test

# Disable swoosh api client as it is only required for production adapters
config :swoosh, :api_client, false

# Print only warnings and errors during test
config :logger, level: :warning

# Initialize plugs at runtime for faster test compilation
config :phoenix, :plug_init_mode, :runtime

# Enable helpful, but potentially expensive runtime checks
config :phoenix_live_view,
  enable_expensive_runtime_checks: true

# Configure Wallaby for E2E testing (works with both FastHTML and Phoenix)
config :wallaby,
  driver: Wallaby.Chrome,
  base_url: System.get_env("TEST_BASE_URL", "http://localhost:5001"),
  # Screenshot path for debugging failed tests
  screenshot_dir: "screenshots/wallaby",
  # Run headless for CI/automation
  hackney_options: [timeout: :infinity, recv_timeout: :infinity],
  chromedriver: [
    capabilities: %{
      chromeOptions: %{
        args: [
          "--headless",
          "--disable-gpu",
          "--no-sandbox",
          "--disable-dev-shm-usage"
        ]
      }
    }
  ]

# Configure PhoenixTest endpoint
config :phoenix_test, :endpoint, QuranSrsWeb.Endpoint
