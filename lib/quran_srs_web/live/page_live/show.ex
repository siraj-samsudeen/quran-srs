defmodule QuranSrsWeb.PageLive.Show do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Page {@page.id}
        <:subtitle>This is a page record from your database.</:subtitle>
        <:actions>
          <.button navigate={~p"/mushafs/#{@current_mushaf}/pages"}>
            <.icon name="hero-arrow-left" />
          </.button>
          <.button
            variant="primary"
            navigate={~p"/mushafs/#{@current_mushaf}/pages/#{@page}/edit?return_to=show"}
          >
            <.icon name="hero-pencil-square" /> Edit page
          </.button>
        </:actions>
      </.header>

      <.list>
        <:item title="Page number">{@page.page_number}</:item>
        <:item title="Juz number">{@page.juz_number}</:item>
        <:item title="Start text">{@page.start_text}</:item>
      </.list>
    </Layouts.app>
    """
  end

  @impl true
  def mount(%{"id" => id, "mushaf_id" => mushaf_id}, _session, socket) do
    mushaf_id = String.to_integer(mushaf_id)
    mushaf = Quran.get_mushaf!(mushaf_id)
    page = Quran.get_page!(id)

    {:ok,
     socket
     |> assign(:page_title, "Show Page - #{mushaf.name}")
     |> assign(:current_mushaf, mushaf)
     |> assign(:page, page)}
  end
end
