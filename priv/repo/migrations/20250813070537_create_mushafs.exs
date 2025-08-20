defmodule QuranSrs.Repo.Migrations.CreateMushafs do
  use Ecto.Migration

  def change do
    create table(:mushafs) do
      add :name, :string
      add :description, :text

      timestamps(type: :utc_datetime)
    end

    create table(:pages) do
      add :page_number, :integer
      add :juz_number, :integer
      add :start_text, :text
      add :mushaf_id, references(:mushafs, on_delete: :nothing)
      
      timestamps(type: :utc_datetime)
    end
    
    create index(:pages, [:mushaf_id])
  end
end
