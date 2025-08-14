defmodule QuranSrsWeb.SurahLive.Show do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Surah {@surah.id}
        <:subtitle>This is a surah record from your database.</:subtitle>
        <:actions>
          <.button navigate={~p"/surahs"}>
            <.icon name="hero-arrow-left" />
          </.button>
          <.button variant="primary" navigate={~p"/surahs/#{@surah}/edit?return_to=show"}>
            <.icon name="hero-pencil-square" /> Edit surah
          </.button>
        </:actions>
      </.header>

      <.list>
        <:item title="Number">{@surah.number}</:item>
        <:item title="Name">{@surah.name}</:item>
        <:item title="Total ayat">{@surah.total_ayat}</:item>
      </.list>
    </Layouts.app>
    """
  end

  @impl true
  def mount(%{"id" => id}, _session, socket) do
    {:ok,
     socket
     |> assign(:page_title, "Show Surah")
     |> assign(:surah, Quran.get_surah!(id))}
  end
end
