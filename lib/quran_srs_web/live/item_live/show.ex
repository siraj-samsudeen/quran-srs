defmodule QuranSrsWeb.ItemLive.Show do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Item {@item.id}
        <:subtitle>This is a item record from your database.</:subtitle>
        <:actions>
          <.button navigate={~p"/items"}>
            <.icon name="hero-arrow-left" />
          </.button>
          <.button variant="primary" navigate={~p"/items/#{@item}/edit?return_to=show"}>
            <.icon name="hero-pencil-square" /> Edit item
          </.button>
        </:actions>
      </.header>

      <.list>
        <:item title="Item type">{@item.item_type}</:item>
        <:item title="Title">{@item.title}</:item>
        <:item title="Start text">{@item.start_text}</:item>
        <:item title="Start line">{@item.start_line}</:item>
        <:item title="End line">{@item.end_line}</:item>
        <:item title="Part number">{@item.part_number}</:item>
        <:item title="Part title">{@item.part_title}</:item>
        <:item title="Tags">{@item.tags}</:item>
      </.list>
    </Layouts.app>
    """
  end

  @impl true
  def mount(%{"id" => id}, _session, socket) do
    {:ok,
     socket
     |> assign(:page_title, "Show Item")
     |> assign(:item, Quran.get_item!(id))}
  end
end
