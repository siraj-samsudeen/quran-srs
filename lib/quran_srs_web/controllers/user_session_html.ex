defmodule QuranSrsWeb.UserSessionHTML do
  use QuranSrsWeb, :html

  embed_templates "user_session_html/*"

  defp local_mail_adapter? do
    Application.get_env(:quran_srs, QuranSrs.Mailer)[:adapter] == Swoosh.Adapters.Local
  end
end
