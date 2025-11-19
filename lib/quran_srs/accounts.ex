defmodule QuranSrs.Accounts do
  use Ash.Domain, otp_app: :quran_srs, extensions: [AshAdmin.Domain]

  admin do
    show? true
  end

  resources do
    resource QuranSrs.Accounts.Token
    resource QuranSrs.Accounts.User
  end
end
