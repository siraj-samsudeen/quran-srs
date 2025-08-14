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
end
