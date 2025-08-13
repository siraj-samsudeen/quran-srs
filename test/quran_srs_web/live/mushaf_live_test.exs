defmodule QuranSrsWeb.MushafLiveTest do
  use QuranSrsWeb.ConnCase

  import Phoenix.LiveViewTest
  import QuranSrs.QuranFixtures

  @create_attrs %{name: "some name", description: "some description"}
  @update_attrs %{name: "some updated name", description: "some updated description"}
  @invalid_attrs %{name: nil, description: nil}
  defp create_mushaf(_) do
    mushaf = mushaf_fixture()

    %{mushaf: mushaf}
  end

  describe "Index" do
    setup [:create_mushaf]

    test "lists all mushafs", %{conn: conn, mushaf: mushaf} do
      {:ok, _index_live, html} = live(conn, ~p"/mushafs")

      assert html =~ "Listing Mushafs"
      assert html =~ mushaf.name
    end

    test "saves new mushaf", %{conn: conn} do
      {:ok, index_live, _html} = live(conn, ~p"/mushafs")

      assert {:ok, form_live, _} =
               index_live
               |> element("a", "New Mushaf")
               |> render_click()
               |> follow_redirect(conn, ~p"/mushafs/new")

      assert render(form_live) =~ "New Mushaf"

      assert form_live
             |> form("#mushaf-form", mushaf: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#mushaf-form", mushaf: @create_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/mushafs")

      html = render(index_live)
      assert html =~ "Mushaf created successfully"
      assert html =~ "some name"
    end

    test "updates mushaf in listing", %{conn: conn, mushaf: mushaf} do
      {:ok, index_live, _html} = live(conn, ~p"/mushafs")

      assert {:ok, form_live, _html} =
               index_live
               |> element("#mushafs-#{mushaf.id} a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/mushafs/#{mushaf}/edit")

      assert render(form_live) =~ "Edit Mushaf"

      assert form_live
             |> form("#mushaf-form", mushaf: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#mushaf-form", mushaf: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/mushafs")

      html = render(index_live)
      assert html =~ "Mushaf updated successfully"
      assert html =~ "some updated name"
    end

    test "deletes mushaf in listing", %{conn: conn, mushaf: mushaf} do
      {:ok, index_live, _html} = live(conn, ~p"/mushafs")

      assert index_live |> element("#mushafs-#{mushaf.id} a", "Delete") |> render_click()
      refute has_element?(index_live, "#mushafs-#{mushaf.id}")
    end
  end

  describe "Show" do
    setup [:create_mushaf]

    test "displays mushaf", %{conn: conn, mushaf: mushaf} do
      {:ok, _show_live, html} = live(conn, ~p"/mushafs/#{mushaf}")

      assert html =~ "Show Mushaf"
      assert html =~ mushaf.name
    end

    test "updates mushaf and returns to show", %{conn: conn, mushaf: mushaf} do
      {:ok, show_live, _html} = live(conn, ~p"/mushafs/#{mushaf}")

      assert {:ok, form_live, _} =
               show_live
               |> element("a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/mushafs/#{mushaf}/edit?return_to=show")

      assert render(form_live) =~ "Edit Mushaf"

      assert form_live
             |> form("#mushaf-form", mushaf: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, show_live, _html} =
               form_live
               |> form("#mushaf-form", mushaf: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/mushafs/#{mushaf}")

      html = render(show_live)
      assert html =~ "Mushaf updated successfully"
      assert html =~ "some updated name"
    end
  end
end
