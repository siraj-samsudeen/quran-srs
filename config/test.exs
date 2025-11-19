import Config
config :quran_srs, token_signing_secret: "B6IcDipLIX/PxW2rXv4C3ka8rgvmEggT"
config :bcrypt_elixir, log_rounds: 1
config :ash, policies: [show_policy_breakdowns?: true], disable_async?: true

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
  secret_key_base: "iXNAESvYOlr7oQeMwAMBGM/9k+M0z7QCN21ciMrXJEYWIv2gSWWhguGqpgbg63mc",
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
