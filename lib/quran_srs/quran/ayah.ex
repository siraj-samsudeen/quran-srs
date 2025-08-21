defmodule QuranSrs.Quran.Ayah do
  use Ecto.Schema
  import Ecto.Changeset

  schema "ayahs" do
    field :ayah_ref, :string
    field :ayah_number, :integer
    field :text_arabic, :string
    field :surah_id, :id

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(ayah, attrs) do
    ayah
    |> cast(attrs, [:ayah_ref, :ayah_number, :text_arabic])
    |> validate_required([:ayah_ref, :ayah_number, :text_arabic])
    |> unique_constraint(:ayah_ref)
  end
end
