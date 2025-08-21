defmodule QuranSrs.Repo.Migrations.CreateItems do
  use Ecto.Migration

  def change do
    create table(:items) do
      add :item_type, :string
      add :title, :string
      add :start_text, :text
      add :start_line, :integer
      add :end_line, :integer
      add :part_number, :integer
      add :part_title, :string
      add :tags, {:array, :string}
      add :page_id, references(:pages, on_delete: :nothing)
      add :surah_id, references(:surahs, on_delete: :nothing)
      add :start_ayah_id, references(:ayahs, on_delete: :nothing)
      add :end_ayah_id, references(:ayahs, on_delete: :nothing)
      add :end_page_id, references(:pages, on_delete: :nothing)
      add :end_surah_id, references(:surahs, on_delete: :nothing)
      add :created_by, references(:users, on_delete: :nothing)

      timestamps(type: :utc_datetime)
    end

    create index(:items, [:page_id])
    create index(:items, [:surah_id])
    create index(:items, [:start_ayah_id])
    create index(:items, [:end_ayah_id])
    create index(:items, [:end_page_id])
    create index(:items, [:end_surah_id])
    create index(:items, [:created_by])
  end
end
