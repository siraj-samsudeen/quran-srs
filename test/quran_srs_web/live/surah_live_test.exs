defmodule QuranSrsWeb.SurahLiveTest do
  use QuranSrsWeb.ConnCase

  import Phoenix.LiveViewTest
  import QuranSrs.QuranFixtures

  @create_attrs %{name: "some name", number: 42, total_ayat: 42}
  @update_attrs %{name: "some updated name", number: 43, total_ayat: 43}
  @invalid_attrs %{name: nil, number: nil, total_ayat: nil}
  defp create_surah(_) do
    surah = surah_fixture()

    %{surah: surah}
  end

  describe "Index" do
    setup [:create_surah]

    test "lists all surahs", %{conn: conn, surah: surah} do
      {:ok, _index_live, html} = live(conn, ~p"/surahs")

      assert html =~ "Listing Surahs"
      assert html =~ surah.name
    end

    test "saves new surah", %{conn: conn} do
      {:ok, index_live, _html} = live(conn, ~p"/surahs")

      assert {:ok, form_live, _} =
               index_live
               |> element("a", "New Surah")
               |> render_click()
               |> follow_redirect(conn, ~p"/surahs/new")

      assert render(form_live) =~ "New Surah"

      assert form_live
             |> form("#surah-form", surah: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#surah-form", surah: @create_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/surahs")

      html = render(index_live)
      assert html =~ "Surah created successfully"
      assert html =~ "some name"
    end

    test "updates surah in listing", %{conn: conn, surah: surah} do
      {:ok, index_live, _html} = live(conn, ~p"/surahs")

      assert {:ok, form_live, _html} =
               index_live
               |> element("#surahs-#{surah.id} a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/surahs/#{surah}/edit")

      assert render(form_live) =~ "Edit Surah"

      assert form_live
             |> form("#surah-form", surah: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#surah-form", surah: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/surahs")

      html = render(index_live)
      assert html =~ "Surah updated successfully"
      assert html =~ "some updated name"
    end

    test "deletes surah in listing", %{conn: conn, surah: surah} do
      {:ok, index_live, _html} = live(conn, ~p"/surahs")

      assert index_live |> element("#surahs-#{surah.id} a", "Delete") |> render_click()
      refute has_element?(index_live, "#surahs-#{surah.id}")
    end
  end

  describe "Show" do
    setup [:create_surah]

    test "displays surah", %{conn: conn, surah: surah} do
      {:ok, _show_live, html} = live(conn, ~p"/surahs/#{surah}")

      assert html =~ "Show Surah"
      assert html =~ surah.name
    end

    test "updates surah and returns to show", %{conn: conn, surah: surah} do
      {:ok, show_live, _html} = live(conn, ~p"/surahs/#{surah}")

      assert {:ok, form_live, _} =
               show_live
               |> element("a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/surahs/#{surah}/edit?return_to=show")

      assert render(form_live) =~ "Edit Surah"

      assert form_live
             |> form("#surah-form", surah: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, show_live, _html} =
               form_live
               |> form("#surah-form", surah: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/surahs/#{surah}")

      html = render(show_live)
      assert html =~ "Surah updated successfully"
      assert html =~ "some updated name"
    end
  end
end
