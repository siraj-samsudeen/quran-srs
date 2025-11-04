defmodule E2ETest do
  use ExUnit.Case, async: false
  use Wallaby.Feature
  import Wallaby.Query

  @moduletag :e2e

  feature "visiting the home page", %{session: session} do
    session
    |> visit("/")
    |> assert_has(css("body"))
  end
end
