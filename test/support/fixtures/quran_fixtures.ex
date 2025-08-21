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

  @doc """
  Generate a surah.
  """
  def surah_fixture(attrs \\ %{}) do
    {:ok, surah} =
      attrs
      |> Enum.into(%{
        name: "some name",
        number: 42,
        total_ayat: 42
      })
      |> QuranSrs.Quran.create_surah()

    surah
  end

  @doc """
  Generate a page.
  """
  def page_fixture(attrs \\ %{}) do
    {:ok, page} =
      attrs
      |> Enum.into(%{
        juz_number: 42,
        page_number: 42,
        start_text: "some start_text",
        mushaf_id: 1
      })
      |> QuranSrs.Quran.create_page()

    page
  end

  @doc """
  Generate a unique ayah ayah_ref.
  """
  def unique_ayah_ayah_ref, do: "some ayah_ref#{System.unique_integer([:positive])}"

  @doc """
  Generate a ayah.
  """
  def ayah_fixture(attrs \\ %{}) do
    {:ok, ayah} =
      attrs
      |> Enum.into(%{
        ayah_number: 42,
        ayah_ref: unique_ayah_ayah_ref(),
        text_arabic: "some text_arabic"
      })
      |> QuranSrs.Quran.create_ayah()

    ayah
  end
end
