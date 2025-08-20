defmodule QuranSrsWeb.PageLiveTest do
  use QuranSrsWeb.ConnCase

  import Phoenix.LiveViewTest
  import QuranSrs.QuranFixtures

  @create_attrs %{page_number: 42, juz_number: 42, start_text: "some start_text", mushaf_id: 1}
  @update_attrs %{page_number: 43, juz_number: 43, start_text: "some updated start_text"}
  @invalid_attrs %{page_number: nil, juz_number: nil, start_text: nil}
  defp create_page(_) do
    page = page_fixture()

    %{page: page}
  end

  describe "Index" do
    setup [:create_page]

    test "lists all pages", %{conn: conn, page: page} do
      {:ok, _index_live, html} = live(conn, ~p"/mushafs/1/pages")

      assert html =~ "Listing Pages"
      assert html =~ page.start_text
    end

    test "saves new page", %{conn: conn} do
      {:ok, index_live, _html} = live(conn, ~p"/mushafs/1/pages")

      assert {:ok, form_live, _} =
               index_live
               |> element("a", "New Page")
               |> render_click()
               |> follow_redirect(conn, ~p"/mushafs/1/pages/new")

      assert render(form_live) =~ "New Page"

      assert form_live
             |> form("#page-form", page: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#page-form", page: @create_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/mushafs/1/pages")

      html = render(index_live)
      assert html =~ "Page created successfully"
      assert html =~ "some start_text"
    end

    test "updates page in listing", %{conn: conn, page: page} do
      {:ok, index_live, _html} = live(conn, ~p"/mushafs/1/pages")

      assert {:ok, form_live, _html} =
               index_live
               |> element("#pages-#{page.id} a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/mushafs/1/pages/#{page}/edit")

      assert render(form_live) =~ "Edit Page"

      assert form_live
             |> form("#page-form", page: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#page-form", page: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/mushafs/1/pages")

      html = render(index_live)
      assert html =~ "Page updated successfully"
      assert html =~ "some updated start_text"
    end

    test "deletes page in listing", %{conn: conn, page: page} do
      {:ok, index_live, _html} = live(conn, ~p"/mushafs/1/pages")

      assert index_live |> element("#pages-#{page.id} a", "Delete") |> render_click()
      refute has_element?(index_live, "#pages-#{page.id}")
    end
  end

  describe "Show" do
    setup [:create_page]

    test "displays page", %{conn: conn, page: page} do
      {:ok, _show_live, html} = live(conn, ~p"/mushafs/1/pages/#{page}")

      assert html =~ "Show Page"
      assert html =~ page.start_text
    end

    test "updates page and returns to show", %{conn: conn, page: page} do
      {:ok, show_live, _html} = live(conn, ~p"/mushafs/1/pages/#{page}")

      assert {:ok, form_live, _} =
               show_live
               |> element("a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/mushafs/1/pages/#{page}/edit?return_to=show")

      assert render(form_live) =~ "Edit Page"

      assert form_live
             |> form("#page-form", page: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, show_live, _html} =
               form_live
               |> form("#page-form", page: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/mushafs/1/pages/#{page}")

      html = render(show_live)
      assert html =~ "Page updated successfully"
      assert html =~ "some updated start_text"
    end
  end
end
