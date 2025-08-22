defmodule QuranSrsWeb.ItemLiveTest do
  use QuranSrsWeb.ConnCase

  import Phoenix.LiveViewTest
  import QuranSrs.QuranFixtures

  @create_attrs %{
    title: "some title",
    end_line: 42,
    item_type: "some item_type",
    start_text: "some start_text",
    start_line: 42,
    part_number: 42,
    part_title: "some part_title",
    tags: ["option1", "option2"]
  }
  @update_attrs %{
    title: "some updated title",
    end_line: 43,
    item_type: "some updated item_type",
    start_text: "some updated start_text",
    start_line: 43,
    part_number: 43,
    part_title: "some updated part_title",
    tags: ["option1"]
  }
  @invalid_attrs %{
    title: nil,
    end_line: nil,
    item_type: nil,
    start_text: nil,
    start_line: nil,
    part_number: nil,
    part_title: nil,
    tags: []
  }
  defp create_item(_) do
    item = item_fixture()

    %{item: item}
  end

  describe "Index" do
    setup [:create_item]

    test "lists all items", %{conn: conn, item: item} do
      {:ok, _index_live, html} = live(conn, ~p"/items")

      assert html =~ "Listing Items"
      assert html =~ item.item_type
    end

    test "saves new item", %{conn: conn} do
      {:ok, index_live, _html} = live(conn, ~p"/items")

      assert {:ok, form_live, _} =
               index_live
               |> element("a", "New Item")
               |> render_click()
               |> follow_redirect(conn, ~p"/items/new")

      assert render(form_live) =~ "New Item"

      assert form_live
             |> form("#item-form", item: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#item-form", item: @create_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/items")

      html = render(index_live)
      assert html =~ "Item created successfully"
      assert html =~ "some item_type"
    end

    test "updates item in listing", %{conn: conn, item: item} do
      {:ok, index_live, _html} = live(conn, ~p"/items")

      assert {:ok, form_live, _html} =
               index_live
               |> element("#items-#{item.id} a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/items/#{item}/edit")

      assert render(form_live) =~ "Edit Item"

      assert form_live
             |> form("#item-form", item: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, index_live, _html} =
               form_live
               |> form("#item-form", item: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/items")

      html = render(index_live)
      assert html =~ "Item updated successfully"
      assert html =~ "some updated item_type"
    end

    test "deletes item in listing", %{conn: conn, item: item} do
      {:ok, index_live, _html} = live(conn, ~p"/items")

      assert index_live |> element("#items-#{item.id} a", "Delete") |> render_click()
      refute has_element?(index_live, "#items-#{item.id}")
    end
  end

  describe "Show" do
    setup [:create_item]

    test "displays item", %{conn: conn, item: item} do
      {:ok, _show_live, html} = live(conn, ~p"/items/#{item}")

      assert html =~ "Show Item"
      assert html =~ item.item_type
    end

    test "updates item and returns to show", %{conn: conn, item: item} do
      {:ok, show_live, _html} = live(conn, ~p"/items/#{item}")

      assert {:ok, form_live, _} =
               show_live
               |> element("a", "Edit")
               |> render_click()
               |> follow_redirect(conn, ~p"/items/#{item}/edit?return_to=show")

      assert render(form_live) =~ "Edit Item"

      assert form_live
             |> form("#item-form", item: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert {:ok, show_live, _html} =
               form_live
               |> form("#item-form", item: @update_attrs)
               |> render_submit()
               |> follow_redirect(conn, ~p"/items/#{item}")

      html = render(show_live)
      assert html =~ "Item updated successfully"
      assert html =~ "some updated item_type"
    end
  end
end
