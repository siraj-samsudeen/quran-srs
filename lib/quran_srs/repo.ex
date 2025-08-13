defmodule QuranSrs.Repo do
  use Ecto.Repo,
    otp_app: :quran_srs,
    adapter: Ecto.Adapters.Postgres
end
