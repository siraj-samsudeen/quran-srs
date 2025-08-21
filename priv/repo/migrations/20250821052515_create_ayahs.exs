defmodule QuranSrs.Repo.Migrations.CreateAyahs do
  use Ecto.Migration

  def change do
    create table(:ayahs) do
      add :ayah_ref, :string
      add :ayah_number, :integer
      add :text_arabic, :text
      add :surah_id, references(:surahs, on_delete: :nothing)

      timestamps(type: :utc_datetime)
    end

    create unique_index(:ayahs, [:ayah_ref])
    create index(:ayahs, [:surah_id])
  end
end
