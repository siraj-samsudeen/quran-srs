defmodule QuranSrs.Quran.Ayah do
  use Ecto.Schema
  import Ecto.Changeset
  
  alias QuranSrs.Quran.Surah

  schema "ayahs" do
    field :ayah_ref, :string
    field :ayah_number, :integer
    field :text_arabic, :string
    belongs_to :surah, Surah

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(ayah, attrs) do
    ayah
    |> cast(attrs, [:ayah_ref, :ayah_number, :text_arabic, :surah_id])
    |> validate_required([:ayah_ref, :ayah_number, :text_arabic, :surah_id])
    |> unique_constraint(:ayah_ref)
  end
end
