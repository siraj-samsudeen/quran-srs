defmodule QuranSrsWeb.MushafLive.Show do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Mushaf {@mushaf.id}
        <:subtitle>This is a mushaf record from your database.</:subtitle>
        <:actions>
          <.button navigate={~p"/mushafs"}>
            <.icon name="hero-arrow-left" />
          </.button>
          <.button variant="primary" navigate={~p"/mushafs/#{@mushaf}/edit?return_to=show"}>
            <.icon name="hero-pencil-square" /> Edit mushaf
          </.button>
        </:actions>
      </.header>

      <.list>
        <:item title="Name">{@mushaf.name}</:item>
        <:item title="Description">{@mushaf.description}</:item>
      </.list>
    </Layouts.app>
    """
  end

  @impl true
  def mount(%{"id" => id}, _session, socket) do
    {:ok,
     socket
     |> assign(:page_title, "Show Mushaf")
     |> assign(:mushaf, Quran.get_mushaf!(id))}
  end
end
