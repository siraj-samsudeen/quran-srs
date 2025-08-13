defmodule QuranSrs.QuranTest do
  use QuranSrs.DataCase

  alias QuranSrs.Quran

  describe "mushafs" do
    alias QuranSrs.Quran.Mushaf

    import QuranSrs.QuranFixtures

    @invalid_attrs %{name: nil, description: nil}

    test "list_mushafs/0 returns all mushafs" do
      mushaf = mushaf_fixture()
      assert Quran.list_mushafs() == [mushaf]
    end

    test "get_mushaf!/1 returns the mushaf with given id" do
      mushaf = mushaf_fixture()
      assert Quran.get_mushaf!(mushaf.id) == mushaf
    end

    test "create_mushaf/1 with valid data creates a mushaf" do
      valid_attrs = %{name: "some name", description: "some description"}

      assert {:ok, %Mushaf{} = mushaf} = Quran.create_mushaf(valid_attrs)
      assert mushaf.name == "some name"
      assert mushaf.description == "some description"
    end

    test "create_mushaf/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Quran.create_mushaf(@invalid_attrs)
    end

    test "update_mushaf/2 with valid data updates the mushaf" do
      mushaf = mushaf_fixture()
      update_attrs = %{name: "some updated name", description: "some updated description"}

      assert {:ok, %Mushaf{} = mushaf} = Quran.update_mushaf(mushaf, update_attrs)
      assert mushaf.name == "some updated name"
      assert mushaf.description == "some updated description"
    end

    test "update_mushaf/2 with invalid data returns error changeset" do
      mushaf = mushaf_fixture()
      assert {:error, %Ecto.Changeset{}} = Quran.update_mushaf(mushaf, @invalid_attrs)
      assert mushaf == Quran.get_mushaf!(mushaf.id)
    end

    test "delete_mushaf/1 deletes the mushaf" do
      mushaf = mushaf_fixture()
      assert {:ok, %Mushaf{}} = Quran.delete_mushaf(mushaf)
      assert_raise Ecto.NoResultsError, fn -> Quran.get_mushaf!(mushaf.id) end
    end

    test "change_mushaf/1 returns a mushaf changeset" do
      mushaf = mushaf_fixture()
      assert %Ecto.Changeset{} = Quran.change_mushaf(mushaf)
    end
  end
end
