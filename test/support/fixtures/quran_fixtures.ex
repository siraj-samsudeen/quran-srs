defmodule QuranSrs.QuranFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `QuranSrs.Quran` context.
  """

  @doc """
  Generate a mushaf.
  """
  def mushaf_fixture(attrs \\ %{}) do
    {:ok, mushaf} =
      attrs
      |> Enum.into(%{
        description: "some description",
        name: "some name"
      })
      |> QuranSrs.Quran.create_mushaf()

    mushaf
  end
end
