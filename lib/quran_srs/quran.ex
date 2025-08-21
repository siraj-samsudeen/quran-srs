defmodule QuranSrs.Quran do
  @moduledoc """
  The Quran context.
  """

  import Ecto.Query, warn: false
  alias QuranSrs.Repo

  alias QuranSrs.Quran.Mushaf

  @doc """
  Returns the list of mushafs.

  ## Examples

      iex> list_mushafs()
      [%Mushaf{}, ...]

  """
  def list_mushafs do
    Repo.all(Mushaf)
  end

  @doc """
  Gets a single mushaf.

  Raises `Ecto.NoResultsError` if the Mushaf does not exist.

  ## Examples

      iex> get_mushaf!(123)
      %Mushaf{}

      iex> get_mushaf!(456)
      ** (Ecto.NoResultsError)

  """
  def get_mushaf!(id), do: Repo.get!(Mushaf, id)

  @doc """
  Creates a mushaf.

  ## Examples

      iex> create_mushaf(%{field: value})
      {:ok, %Mushaf{}}

      iex> create_mushaf(%{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def create_mushaf(attrs) do
    %Mushaf{}
    |> Mushaf.changeset(attrs)
    |> Repo.insert()
  end

  @doc """
  Updates a mushaf.

  ## Examples

      iex> update_mushaf(mushaf, %{field: new_value})
      {:ok, %Mushaf{}}

      iex> update_mushaf(mushaf, %{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def update_mushaf(%Mushaf{} = mushaf, attrs) do
    mushaf
    |> Mushaf.changeset(attrs)
    |> Repo.update()
  end

  @doc """
  Deletes a mushaf.

  ## Examples

      iex> delete_mushaf(mushaf)
      {:ok, %Mushaf{}}

      iex> delete_mushaf(mushaf)
      {:error, %Ecto.Changeset{}}

  """
  def delete_mushaf(%Mushaf{} = mushaf) do
    Repo.delete(mushaf)
  end

  @doc """
  Returns an `%Ecto.Changeset{}` for tracking mushaf changes.

  ## Examples

      iex> change_mushaf(mushaf)
      %Ecto.Changeset{data: %Mushaf{}}

  """
  def change_mushaf(%Mushaf{} = mushaf, attrs \\ %{}) do
    Mushaf.changeset(mushaf, attrs)
  end

  alias QuranSrs.Quran.Surah

  @doc """
  Returns the list of surahs.

  ## Examples

      iex> list_surahs()
      [%Surah{}, ...]

  """
  def list_surahs do
    Repo.all(Surah)
  end

  @doc """
  Gets a single surah.

  Raises `Ecto.NoResultsError` if the Surah does not exist.

  ## Examples

      iex> get_surah!(123)
      %Surah{}

      iex> get_surah!(456)
      ** (Ecto.NoResultsError)

  """
  def get_surah!(id), do: Repo.get!(Surah, id)

  @doc """
  Creates a surah.

  ## Examples

      iex> create_surah(%{field: value})
      {:ok, %Surah{}}

      iex> create_surah(%{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def create_surah(attrs) do
    %Surah{}
    |> Surah.changeset(attrs)
    |> Repo.insert()
  end

  @doc """
  Updates a surah.

  ## Examples

      iex> update_surah(surah, %{field: new_value})
      {:ok, %Surah{}}

      iex> update_surah(surah, %{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def update_surah(%Surah{} = surah, attrs) do
    surah
    |> Surah.changeset(attrs)
    |> Repo.update()
  end

  @doc """
  Deletes a surah.

  ## Examples

      iex> delete_surah(surah)
      {:ok, %Surah{}}

      iex> delete_surah(surah)
      {:error, %Ecto.Changeset{}}

  """
  def delete_surah(%Surah{} = surah) do
    Repo.delete(surah)
  end

  @doc """
  Returns an `%Ecto.Changeset{}` for tracking surah changes.

  ## Examples

      iex> change_surah(surah)
      %Ecto.Changeset{data: %Surah{}}

  """
  def change_surah(%Surah{} = surah, attrs \\ %{}) do
    Surah.changeset(surah, attrs)
  end

  alias QuranSrs.Quran.Page

  @doc """
  Returns the list of pages.

  ## Examples

      iex> list_pages()
      [%Page{}, ...]

  """
  def list_pages do
    Repo.all(Page)
  end

  def list_pages_by_mushaf(mushaf_id) do
    Page
    |> where([p], p.mushaf_id == ^mushaf_id)
    |> order_by([p], p.page_number)
    |> Repo.all()
  end

  @doc """
  Gets a single page.

  Raises `Ecto.NoResultsError` if the Page does not exist.

  ## Examples

      iex> get_page!(123)
      %Page{}

      iex> get_page!(456)
      ** (Ecto.NoResultsError)

  """
  def get_page!(id), do: Repo.get!(Page, id)

  @doc """
  Creates a page.

  ## Examples

      iex> create_page(%{field: value})
      {:ok, %Page{}}

      iex> create_page(%{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def create_page(attrs) do
    %Page{}
    |> Page.changeset(attrs)
    |> Repo.insert()
  end

  @doc """
  Updates a page.

  ## Examples

      iex> update_page(page, %{field: new_value})
      {:ok, %Page{}}

      iex> update_page(page, %{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def update_page(%Page{} = page, attrs) do
    page
    |> Page.changeset(attrs)
    |> Repo.update()
  end

  @doc """
  Deletes a page.

  ## Examples

      iex> delete_page(page)
      {:ok, %Page{}}

      iex> delete_page(page)
      {:error, %Ecto.Changeset{}}

  """
  def delete_page(%Page{} = page) do
    Repo.delete(page)
  end

  @doc """
  Returns an `%Ecto.Changeset{}` for tracking page changes.

  ## Examples

      iex> change_page(page)
      %Ecto.Changeset{data: %Page{}}

  """
  def change_page(%Page{} = page, attrs \\ %{}) do
    Page.changeset(page, attrs)
  end

  alias QuranSrs.Quran.Ayah

  @doc """
  Returns the list of ayahs.

  ## Examples

      iex> list_ayahs()
      [%Ayah{}, ...]

  """
  def list_ayahs do
    Ayah
    |> preload(:surah)
    |> Repo.all()
  end

  @doc """
  Gets a single ayah.

  Raises `Ecto.NoResultsError` if the Ayah does not exist.

  ## Examples

      iex> get_ayah!(123)
      %Ayah{}

      iex> get_ayah!(456)
      ** (Ecto.NoResultsError)

  """
  def get_ayah!(id) do
    Ayah
    |> preload(:surah)
    |> Repo.get!(id)
  end

  @doc """
  Creates a ayah.

  ## Examples

      iex> create_ayah(%{field: value})
      {:ok, %Ayah{}}

      iex> create_ayah(%{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def create_ayah(attrs) do
    %Ayah{}
    |> Ayah.changeset(attrs)
    |> Repo.insert()
  end

  @doc """
  Updates a ayah.

  ## Examples

      iex> update_ayah(ayah, %{field: new_value})
      {:ok, %Ayah{}}

      iex> update_ayah(ayah, %{field: bad_value})
      {:error, %Ecto.Changeset{}}

  """
  def update_ayah(%Ayah{} = ayah, attrs) do
    ayah
    |> Ayah.changeset(attrs)
    |> Repo.update()
  end

  @doc """
  Deletes a ayah.

  ## Examples

      iex> delete_ayah(ayah)
      {:ok, %Ayah{}}

      iex> delete_ayah(ayah)
      {:error, %Ecto.Changeset{}}

  """
  def delete_ayah(%Ayah{} = ayah) do
    Repo.delete(ayah)
  end

  @doc """
  Returns an `%Ecto.Changeset{}` for tracking ayah changes.

  ## Examples

      iex> change_ayah(ayah)
      %Ecto.Changeset{data: %Ayah{}}

  """
  def change_ayah(%Ayah{} = ayah, attrs \\ %{}) do
    Ayah.changeset(ayah, attrs)
  end

  @doc """
  Returns a list of surahs for select options with number and name.

  ## Examples

      iex> list_surah_options()
      [{"1. Al-Fatihah", 1}, {"2. Al-Baqarah", 2}, ...]

  """
  def list_surah_options do
    Surah
    |> select([s], {s.number, s.name, s.id})
    |> order_by([s], s.number)
    |> Repo.all()
    |> Enum.map(fn {number, name, id} -> 
      {"#{number}. #{name}", id}
    end)
  end
end
