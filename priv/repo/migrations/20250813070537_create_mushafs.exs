defmodule QuranSrs.Repo.Migrations.CreateMushafs do
  use Ecto.Migration

  def change do
    create table(:mushafs) do
      add :name, :string
      add :description, :text

      timestamps(type: :utc_datetime)
    end
  end
end
