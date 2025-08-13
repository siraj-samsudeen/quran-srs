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
end
