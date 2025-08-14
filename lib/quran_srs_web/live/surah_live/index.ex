defmodule QuranSrsWeb.SurahLive.Index do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Listing Surahs
        <:actions>
          <.button variant="primary" navigate={~p"/surahs/new"}>
            <.icon name="hero-plus" /> New Surah
          </.button>
        </:actions>
      </.header>

      <.table
        id="surahs"
        rows={@streams.surahs}
        row_click={fn {_id, surah} -> JS.navigate(~p"/surahs/#{surah}") end}
      >
        <:col :let={{_id, surah}} label="Number">{surah.number}</:col>
        <:col :let={{_id, surah}} label="Name">{surah.name}</:col>
        <:col :let={{_id, surah}} label="Total ayat">{surah.total_ayat}</:col>
        <:action :let={{_id, surah}}>
          <div class="sr-only">
            <.link navigate={~p"/surahs/#{surah}"}>Show</.link>
          </div>
          <.link navigate={~p"/surahs/#{surah}/edit"}>Edit</.link>
        </:action>
        <:action :let={{id, surah}}>
          <.link
            phx-click={JS.push("delete", value: %{id: surah.id}) |> hide("##{id}")}
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
     |> assign(:page_title, "Listing Surahs")
     |> stream(:surahs, Quran.list_surahs())}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    surah = Quran.get_surah!(id)
    {:ok, _} = Quran.delete_surah(surah)

    {:noreply, stream_delete(socket, :surahs, surah)}
  end
end
