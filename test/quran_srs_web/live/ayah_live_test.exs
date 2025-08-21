defmodule QuranSrsWeb.AyahLiveTest do
  use QuranSrsWeb.ConnCase

  import Phoenix.LiveViewTest
  import QuranSrs.QuranFixtures

  defp create_attrs_with_surah(surah) do
    %{ayah_ref: "some ayah_ref", ayah_number: 42, text_arabic: "some text_arabic", surah_id: surah.id}
  end

  @update_attrs %{ayah_ref: "some updated ayah_ref", ayah_number: 43, text_arabic: "some updated text_arabic"}
  @invalid_attrs %{ayah_ref: nil, ayah_number: nil, text_arabic: nil}
  defp create_ayah(_) do
    ayah = ayah_fixture()

    %{ayah: ayah}
  end

  describe "Index" do
    setup [:create_ayah]

    test "lists all ayahs", %{conn: conn, ayah: ayah} do
      {:ok, _index_live, html} = live(conn, ~p"/ayahs")

      assert html =~ "Listing Ayahs"
      assert html =~ ayah.ayah_ref
    end

    test "saves new ayah", %{conn: conn} do
      surah = surah_fixture()
      create_attrs = create_attrs_with_surah(surah)
      
      {:ok, index_live, _html} = live(conn, ~p"/ayahs")

      assert {:ok, form_live, _} =
               index_live
               |> element("a", "New Ayah")
               |> render_click()
               |> follow_redirect(conn, ~p"/ayahs/new")

      assert render(form_live) =~ "New Ayah"

      assert form_live
             |> form("#ayah-form", ayah: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#ayah-form", ayah: create_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/ayahs")

      html = render(index_live)
      assert html =~ "Ayah created successfully"
      assert html =~ "some ayah_ref"
    end

    test "updates ayah in listing", %{conn: conn, ayah: ayah} do
      {:ok, index_live, _html} = live(conn, ~p"/ayahs")

      assert {:ok, form_live, _html} =
               index_live
               |> element("#ayahs-#{ayah.id} a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/ayahs/#{ayah}/edit")

      assert render(form_live) =~ "Edit Ayah"

      assert form_live
             |> form("#ayah-form", ayah: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#ayah-form", ayah: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/ayahs")

      html = render(index_live)
      assert html =~ "Ayah updated successfully"
      assert html =~ "some updated ayah_ref"
    end

    test "deletes ayah in listing", %{conn: conn, ayah: ayah} do
      {:ok, index_live, _html} = live(conn, ~p"/ayahs")

      assert index_live |> element("#ayahs-#{ayah.id} a", "Delete") |> render_click()
      refute has_element?(index_live, "#ayahs-#{ayah.id}")
    end
  end

  describe "Show" do
    setup [:create_ayah]

    test "displays ayah", %{conn: conn, ayah: ayah} do
      {:ok, _show_live, html} = live(conn, ~p"/ayahs/#{ayah}")

      assert html =~ "Show Ayah"
      assert html =~ ayah.ayah_ref
    end

    test "updates ayah and returns to show", %{conn: conn, ayah: ayah} do
      {:ok, show_live, _html} = live(conn, ~p"/ayahs/#{ayah}")

      assert {:ok, form_live, _} =
               show_live
               |> element("a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/ayahs/#{ayah}/edit?return_to=show")

      assert render(form_live) =~ "Edit Ayah"

      assert form_live
             |> form("#ayah-form", ayah: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, show_live, _html} =
               form_live
               |> form("#ayah-form", ayah: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/ayahs/#{ayah}")

      html = render(show_live)
      assert html =~ "Ayah updated successfully"
      assert html =~ "some updated ayah_ref"
    end
  end
end
