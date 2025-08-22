defmodule QuranSrs.Repo.Migrations.CreateMushafs do
  use Ecto.Migration

  def change do
    # Master data tables in dependency order

    create table(:mushafs) do
      add :name, :string
      add :description, :text

      timestamps(type: :utc_datetime)
    end

    create table(:surahs) do
      add :number, :integer
      add :name, :string
      add :total_ayat, :integer

      timestamps(type: :utc_datetime)
    end

    create table(:pages) do
      add :page_number, :integer
      add :juz_number, :integer
      add :start_text, :text
      add :mushaf_id, references(:mushafs, on_delete: :nothing)

      timestamps(type: :utc_datetime)
    end

    create table(:ayahs) do
      add :ayah_ref, :string
      add :ayah_number, :integer
      add :text_arabic, :text
      add :surah_id, references(:surahs, on_delete: :nothing)

      timestamps(type: :utc_datetime)
    end

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
      add :created_by_id, references(:users, on_delete: :nothing)

      timestamps(type: :utc_datetime)
    end

    # Indexes
    create index(:pages, [:mushaf_id])
    create index(:ayahs, [:surah_id])
    create unique_index(:ayahs, [:ayah_ref])
    create unique_index(:ayahs, [:surah_id, :ayah_number])
    create index(:items, [:page_id])
    create index(:items, [:surah_id])
    create index(:items, [:start_ayah_id])
    create index(:items, [:end_ayah_id])
    create index(:items, [:end_page_id])
    create index(:items, [:end_surah_id])
    create index(:items, [:created_by_id])
  end
end
