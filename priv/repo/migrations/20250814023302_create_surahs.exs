defmodule QuranSrs.Repo.Migrations.CreateSurahs do
  use Ecto.Migration

  def change do
    create table(:surahs) do
      add :number, :integer
      add :name, :string
      add :total_ayat, :integer

      timestamps(type: :utc_datetime)
    end
  end
end
