defmodule QuranSrsWeb.MushafLive.Index do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Listing Mushafs
        <:actions>
          <.button variant="primary" navigate={~p"/mushafs/new"}>
            <.icon name="hero-plus" /> New Mushaf
          </.button>
        </:actions>
      </.header>

      <.table
        id="mushafs"
        rows={@streams.mushafs}
        row_click={fn {_id, mushaf} -> JS.navigate(~p"/mushafs/#{mushaf}") end}
      >
        <:col :let={{_id, mushaf}} label="Name">{mushaf.name}</:col>
        <:col :let={{_id, mushaf}} label="Description">{mushaf.description}</:col>
        <:action :let={{_id, mushaf}}>
          <div class="sr-only">
            <.link navigate={~p"/mushafs/#{mushaf}"}>Show</.link>
          </div>
          <.link navigate={~p"/mushafs/#{mushaf}/edit"}>Edit</.link>
        </:action>
        <:action :let={{id, mushaf}}>
          <.link
            phx-click={JS.push("delete", value: %{id: mushaf.id}) |> hide("##{id}")}
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
     |> assign(:page_title, "Listing Mushafs")
     |> stream(:mushafs, Quran.list_mushafs())}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    mushaf = Quran.get_mushaf!(id)
    {:ok, _} = Quran.delete_mushaf(mushaf)

    {:noreply, stream_delete(socket, :mushafs, mushaf)}
  end
end
