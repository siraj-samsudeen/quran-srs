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

  describe "surahs" do
    alias QuranSrs.Quran.Surah

    import QuranSrs.QuranFixtures

    @invalid_attrs %{name: nil, number: nil, total_ayat: nil}

    test "list_surahs/0 returns all surahs" do
      surah = surah_fixture()
      assert Quran.list_surahs() == [surah]
    end

    test "get_surah!/1 returns the surah with given id" do
      surah = surah_fixture()
      assert Quran.get_surah!(surah.id) == surah
    end

    test "create_surah/1 with valid data creates a surah" do
      valid_attrs = %{name: "some name", number: 42, total_ayat: 42}

      assert {:ok, %Surah{} = surah} = Quran.create_surah(valid_attrs)
      assert surah.name == "some name"
      assert surah.number == 42
      assert surah.total_ayat == 42
    end

    test "create_surah/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Quran.create_surah(@invalid_attrs)
    end

    test "update_surah/2 with valid data updates the surah" do
      surah = surah_fixture()
      update_attrs = %{name: "some updated name", number: 43, total_ayat: 43}

      assert {:ok, %Surah{} = surah} = Quran.update_surah(surah, update_attrs)
      assert surah.name == "some updated name"
      assert surah.number == 43
      assert surah.total_ayat == 43
    end

    test "update_surah/2 with invalid data returns error changeset" do
      surah = surah_fixture()
      assert {:error, %Ecto.Changeset{}} = Quran.update_surah(surah, @invalid_attrs)
      assert surah == Quran.get_surah!(surah.id)
    end

    test "delete_surah/1 deletes the surah" do
      surah = surah_fixture()
      assert {:ok, %Surah{}} = Quran.delete_surah(surah)
      assert_raise Ecto.NoResultsError, fn -> Quran.get_surah!(surah.id) end
    end

    test "change_surah/1 returns a surah changeset" do
      surah = surah_fixture()
      assert %Ecto.Changeset{} = Quran.change_surah(surah)
    end
  end
end
