defmodule QuranSrs.Quran.Item do
  use Ecto.Schema
  import Ecto.Changeset

  schema "items" do
    field :item_type, :string
    field :title, :string
    field :start_text, :string
    field :start_line, :integer
    field :end_line, :integer
    field :part_number, :integer
    field :part_title, :string
    field :tags, {:array, :string}
    field :page_id, :id
    field :surah_id, :id
    field :start_ayah_id, :id
    field :end_ayah_id, :id
    field :end_page_id, :id
    field :end_surah_id, :id
    field :created_by, :id

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(item, attrs) do
    item
    |> cast(attrs, [
      :item_type,
      :title,
      :start_text,
      :start_line,
      :end_line,
      :part_number,
      :part_title,
      :tags
    ])
    |> validate_required([
      :item_type,
      :title,
      :start_text,
      :start_line,
      :end_line,
      :part_number,
      :part_title,
      :tags
    ])
  end
end
