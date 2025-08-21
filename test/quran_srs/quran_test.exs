defmodule QuranSrs.QuranTest do
  use QuranSrs.DataCase

  alias QuranSrs.Quran

  describe "mushafs" do
    alias QuranSrs.Quran.Mushaf

    import QuranSrs.QuranFixtures

    @invalid_attrs %{name: nil, description: nil}

    test "list_mushafs/0 returns all mushafs" do
      mushaf = mushaf_fixture()
      # Master data from migrations also present
      assert mushaf in Quran.list_mushafs()
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
      # Master data from migrations also present
      assert surah in Quran.list_surahs()
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

  describe "pages" do
    alias QuranSrs.Quran.Page

    import QuranSrs.QuranFixtures

    @invalid_attrs %{page_number: nil, juz_number: nil, start_text: nil}

    test "list_pages/0 returns all pages" do
      page = page_fixture()
      # Master data from migrations also present
      assert page in Quran.list_pages()
    end

    test "get_page!/1 returns the page with given id" do
      page = page_fixture()
      assert Quran.get_page!(page.id) == page
    end

    test "create_page/1 with valid data creates a page" do
      valid_attrs = %{page_number: 42, juz_number: 42, start_text: "some start_text", mushaf_id: 1}

      assert {:ok, %Page{} = page} = Quran.create_page(valid_attrs)
      assert page.page_number == 42
      assert page.juz_number == 42
      assert page.start_text == "some start_text"
    end

    test "create_page/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Quran.create_page(@invalid_attrs)
    end

    test "update_page/2 with valid data updates the page" do
      page = page_fixture()
      update_attrs = %{page_number: 43, juz_number: 43, start_text: "some updated start_text"}

      assert {:ok, %Page{} = page} = Quran.update_page(page, update_attrs)
      assert page.page_number == 43
      assert page.juz_number == 43
      assert page.start_text == "some updated start_text"
    end

    test "update_page/2 with invalid data returns error changeset" do
      page = page_fixture()
      assert {:error, %Ecto.Changeset{}} = Quran.update_page(page, @invalid_attrs)
      assert page == Quran.get_page!(page.id)
    end

    test "delete_page/1 deletes the page" do
      page = page_fixture()
      assert {:ok, %Page{}} = Quran.delete_page(page)
      assert_raise Ecto.NoResultsError, fn -> Quran.get_page!(page.id) end
    end

    test "change_page/1 returns a page changeset" do
      page = page_fixture()
      assert %Ecto.Changeset{} = Quran.change_page(page)
    end
  end

  describe "ayahs" do
    alias QuranSrs.Quran.Ayah

    import QuranSrs.QuranFixtures

    @invalid_attrs %{ayah_ref: nil, ayah_number: nil, text_arabic: nil}

    test "list_ayahs/0 returns all ayahs" do
      ayah = ayah_fixture()
      ayahs = Quran.list_ayahs()
      
      # Can't use == comparison because list_ayahs/0 preloads :surah association
      assert length(ayahs) == 1
      [fetched_ayah] = ayahs
      assert fetched_ayah.id == ayah.id
      assert fetched_ayah.ayah_ref == ayah.ayah_ref
    end

    test "get_ayah!/1 returns the ayah with given id" do
      ayah = ayah_fixture()
      fetched_ayah = Quran.get_ayah!(ayah.id)
      
      # Can't use == comparison because get_ayah!/1 preloads :surah association
      # while the fixture returns ayah without preloaded associations
      assert fetched_ayah.id == ayah.id
      assert fetched_ayah.ayah_ref == ayah.ayah_ref
      assert fetched_ayah.surah_id == ayah.surah_id
    end

    test "create_ayah/1 with valid data creates a ayah" do
      surah = surah_fixture()
      valid_attrs = %{ayah_ref: "some ayah_ref", ayah_number: 42, text_arabic: "some text_arabic", surah_id: surah.id}

      assert {:ok, %Ayah{} = ayah} = Quran.create_ayah(valid_attrs)
      assert ayah.ayah_ref == "some ayah_ref"
      assert ayah.ayah_number == 42
      assert ayah.text_arabic == "some text_arabic"
      assert ayah.surah_id == surah.id
    end

    test "create_ayah/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Quran.create_ayah(@invalid_attrs)
    end

    test "update_ayah/2 with valid data updates the ayah" do
      ayah = ayah_fixture()
      update_attrs = %{ayah_ref: "some updated ayah_ref", ayah_number: 43, text_arabic: "some updated text_arabic"}

      assert {:ok, %Ayah{} = ayah} = Quran.update_ayah(ayah, update_attrs)
      assert ayah.ayah_ref == "some updated ayah_ref"
      assert ayah.ayah_number == 43
      assert ayah.text_arabic == "some updated text_arabic"
    end

    test "update_ayah/2 with invalid data returns error changeset" do
      ayah = ayah_fixture()
      assert {:error, %Ecto.Changeset{}} = Quran.update_ayah(ayah, @invalid_attrs)
      
      # Verify the ayah wasn't changed in the database
      fetched_ayah = Quran.get_ayah!(ayah.id)
      assert fetched_ayah.ayah_ref == ayah.ayah_ref
      assert fetched_ayah.ayah_number == ayah.ayah_number
    end

    test "delete_ayah/1 deletes the ayah" do
      ayah = ayah_fixture()
      assert {:ok, %Ayah{}} = Quran.delete_ayah(ayah)
      assert_raise Ecto.NoResultsError, fn -> Quran.get_ayah!(ayah.id) end
    end

    test "change_ayah/1 returns a ayah changeset" do
      ayah = ayah_fixture()
      assert %Ecto.Changeset{} = Quran.change_ayah(ayah)
    end
  end

  describe "items" do
    alias QuranSrs.Quran.Item

    import QuranSrs.QuranFixtures

    @invalid_attrs %{title: nil, end_line: nil, item_type: nil, start_text: nil, start_line: nil, part_number: nil, part_title: nil, tags: nil}

    test "list_items/0 returns all items" do
      item = item_fixture()
      assert Quran.list_items() == [item]
    end

    test "get_item!/1 returns the item with given id" do
      item = item_fixture()
      assert Quran.get_item!(item.id) == item
    end

    test "create_item/1 with valid data creates a item" do
      valid_attrs = %{title: "some title", end_line: 42, item_type: "some item_type", start_text: "some start_text", start_line: 42, part_number: 42, part_title: "some part_title", tags: ["option1", "option2"]}

      assert {:ok, %Item{} = item} = Quran.create_item(valid_attrs)
      assert item.title == "some title"
      assert item.end_line == 42
      assert item.item_type == "some item_type"
      assert item.start_text == "some start_text"
      assert item.start_line == 42
      assert item.part_number == 42
      assert item.part_title == "some part_title"
      assert item.tags == ["option1", "option2"]
    end

    test "create_item/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Quran.create_item(@invalid_attrs)
    end

    test "update_item/2 with valid data updates the item" do
      item = item_fixture()
      update_attrs = %{title: "some updated title", end_line: 43, item_type: "some updated item_type", start_text: "some updated start_text", start_line: 43, part_number: 43, part_title: "some updated part_title", tags: ["option1"]}

      assert {:ok, %Item{} = item} = Quran.update_item(item, update_attrs)
      assert item.title == "some updated title"
      assert item.end_line == 43
      assert item.item_type == "some updated item_type"
      assert item.start_text == "some updated start_text"
      assert item.start_line == 43
      assert item.part_number == 43
      assert item.part_title == "some updated part_title"
      assert item.tags == ["option1"]
    end

    test "update_item/2 with invalid data returns error changeset" do
      item = item_fixture()
      assert {:error, %Ecto.Changeset{}} = Quran.update_item(item, @invalid_attrs)
      assert item == Quran.get_item!(item.id)
    end

    test "delete_item/1 deletes the item" do
      item = item_fixture()
      assert {:ok, %Item{}} = Quran.delete_item(item)
      assert_raise Ecto.NoResultsError, fn -> Quran.get_item!(item.id) end
    end

    test "change_item/1 returns a item changeset" do
      item = item_fixture()
      assert %Ecto.Changeset{} = Quran.change_item(item)
    end
  end
end
