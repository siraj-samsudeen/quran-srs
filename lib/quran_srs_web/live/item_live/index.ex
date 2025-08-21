defmodule QuranSrsWeb.ItemLive.Index do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Listing Items
        <:actions>
          <.button variant="primary" navigate={~p"/items/new"}>
            <.icon name="hero-plus" /> New Item
          </.button>
        </:actions>
      </.header>

      <.table
        id="items"
        rows={@streams.items}
        row_click={fn {_id, item} -> JS.navigate(~p"/items/#{item}") end}
      >
        <:col :let={{_id, item}} label="Item type">{item.item_type}</:col>
        <:col :let={{_id, item}} label="Title">{item.title}</:col>
        <:col :let={{_id, item}} label="Start text">{item.start_text}</:col>
        <:col :let={{_id, item}} label="Start line">{item.start_line}</:col>
        <:col :let={{_id, item}} label="End line">{item.end_line}</:col>
        <:col :let={{_id, item}} label="Part number">{item.part_number}</:col>
        <:col :let={{_id, item}} label="Part title">{item.part_title}</:col>
        <:col :let={{_id, item}} label="Tags">{item.tags}</:col>
        <:action :let={{_id, item}}>
          <div class="sr-only">
            <.link navigate={~p"/items/#{item}"}>Show</.link>
          </div>
          <.link navigate={~p"/items/#{item}/edit"}>Edit</.link>
        </:action>
        <:action :let={{id, item}}>
          <.link
            phx-click={JS.push("delete", value: %{id: item.id}) |> hide("##{id}")}
            data-confirm="Are you sure?"
          >
            Delete
          </.link>
        </:action>
      </.table>
    </Layouts.app>
    """
  end

  @impl true
  def mount(_params, _session, socket) do
    {:ok,
     socket
     |> assign(:page_title, "Listing Items")
     |> stream(:items, Quran.list_items())}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    item = Quran.get_item!(id)
    {:ok, _} = Quran.delete_item(item)

    {:noreply, stream_delete(socket, :items, item)}
  end
end
