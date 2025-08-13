defmodule QuranSrs.Quran.Mushaf do
  use Ecto.Schema
  import Ecto.Changeset

  schema "mushafs" do
    field :name, :string
    field :description, :string

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(mushaf, attrs) do
    mushaf
    |> cast(attrs, [:name, :description])
    |> validate_required([:name, :description])
  end
end
