defmodule QuranSrs.Repo.Migrations.SeedMasterData do
  use Ecto.Migration

  require Explorer.DataFrame, as: DF
  alias QuranSrs.{Repo, Quran}

  def up do
    # Seed core master data required for application functionality
    # This data is essential business data that should exist in all environments
    seed_mushafs()
    seed_surahs()
    seed_pages()
    seed_items()
  end

  def down do
    # Remove master data in reverse dependency order
    Repo.delete_all(Quran.Item)
    Repo.delete_all(Quran.Page)
    Repo.delete_all(Quran.Surah)
    Repo.delete_all(Quran.Mushaf)
  end

  defp seed_mushafs do
    mushafs = [
      %{
        name: "Madinah Mushaf",
        description: "Standard Madinah Mushaf with 604 pages"
      },
      %{
        name: "Indo-Pak 15-Line",
        description: "Indian/Pakistani Mushaf with 15 lines per page"
      }
    ]

    Enum.each(mushafs, &Quran.create_mushaf/1)
  end

  defp seed_surahs do
    load_master_data_csv("surahs.csv")
    |> Enum.each(&Quran.create_surah/1)
  end

  defp seed_pages do
    load_master_data_csv("pages.csv")
    |> Enum.each(&Quran.create_page/1)
  end

  defp seed_items do
    load_master_data_csv("items.csv")
    |> Enum.each(&Quran.create_item/1)
  end

  defp load_master_data_csv(filename) do
    Path.join([:code.priv_dir(:quran_srs), "repo", "master_data", filename])
    |> DF.from_csv!()
    |> DF.to_rows()
  end
end
