defmodule QuranSrs.Secrets do
  use AshAuthentication.Secret

  def secret_for(
        [:authentication, :tokens, :signing_secret],
        QuranSrs.Accounts.User,
        _opts,
        _context
      ) do
    Application.fetch_env(:quran_srs, :token_signing_secret)
  end
end
