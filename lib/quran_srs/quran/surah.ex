defmodule QuranSrs.Quran.Surah do
  use Ecto.Schema
  import Ecto.Changeset

  schema "surahs" do
    field :number, :integer
    field :name, :string
    field :total_ayat, :integer

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(surah, attrs) do
    surah
    |> cast(attrs, [:number, :name, :total_ayat])
    |> validate_required([:number, :name, :total_ayat])
  end
end
