defmodule E2ETest do
  use ExUnit.Case, async: false
  use Wallaby.Feature
  import Wallaby.Query

  @moduletag :e2e

  defp login(session, email \\ "mailsiraj@gmail.com", password \\ "123") do
    session
    |> fill_in(css("input[name='email']"), with: email)
    |> fill_in(css("input[name='password']"), with: password)
    |> click(css("button[type='submit']"))
  end

  defp select_first_hafiz(session) do
    session
    |> click(css("button", text: "Switch Hafiz", at: 0))
  end

  feature "Full Cycle mode is always visible", %{session: session} do
    session
    |> visit("/")
    |> login()
    |> select_first_hafiz()
    |> assert_has(css("[data-testid='mode-full-cycle']"))
  end
end
