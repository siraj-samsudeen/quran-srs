defmodule QuranSrsWeb.PageLive.Index do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Listing Pages - {@current_mushaf.name}
        <:actions>
          <.button variant="primary" navigate={~p"/mushafs/#{@current_mushaf}/pages/new"}>
            <.icon name="hero-plus" /> New Page
          </.button>
        </:actions>
      </.header>

      <.table
        id="pages"
        rows={@streams.pages}
        row_click={fn {_id, page} -> JS.navigate(~p"/mushafs/#{@current_mushaf}/pages/#{page}") end}
      >
        <:col :let={{_id, page}} label="Page number">{page.page_number}</:col>
        <:col :let={{_id, page}} label="Juz number">{page.juz_number}</:col>
        <:col :let={{_id, page}} label="Start text">{page.start_text}</:col>
        <:action :let={{_id, page}}>
          <div class="sr-only">
            <.link navigate={~p"/mushafs/#{@current_mushaf}/pages/#{page}"}>Show</.link>
          </div>
          <.link navigate={~p"/mushafs/#{@current_mushaf}/pages/#{page}/edit"}>Edit</.link>
        </:action>
        <:action :let={{id, page}}>
          <.link
            phx-click={JS.push("delete", value: %{id: page.id}) |> hide("##{id}")}
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
  def mount(%{"mushaf_id" => mushaf_id}, _session, socket) do
    mushaf_id = String.to_integer(mushaf_id)
    mushaf = Quran.get_mushaf!(mushaf_id)
    pages = Quran.list_pages_by_mushaf(mushaf_id)
    
    {:ok,
     socket
     |> assign(:page_title, "Listing Pages - #{mushaf.name}")
     |> assign(:current_mushaf, mushaf)
     |> stream(:pages, pages)}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    page = Quran.get_page!(id)
    {:ok, _} = Quran.delete_page(page)

    {:noreply, stream_delete(socket, :pages, page)}
  end
end
