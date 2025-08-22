defmodule QuranSrs.Quran.Page do
  use Ecto.Schema
  import Ecto.Changeset

  schema "pages" do
    field :page_number, :integer
    field :juz_number, :integer
    field :start_text, :string
    belongs_to :mushaf, QuranSrs.Quran.Mushaf

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(page, attrs) do
    page
    |> cast(attrs, [:page_number, :juz_number, :start_text, :mushaf_id])
    |> validate_required([:page_number, :juz_number, :start_text, :mushaf_id])
  end
end
