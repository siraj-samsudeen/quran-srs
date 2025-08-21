defmodule QuranSrsWeb.AyahLive.Show do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Ayah {@ayah.id}
        <:subtitle>This is a ayah record from your database.</:subtitle>
        <:actions>
          <.button navigate={~p"/ayahs"}>
            <.icon name="hero-arrow-left" />
          </.button>
          <.button variant="primary" navigate={~p"/ayahs/#{@ayah}/edit?return_to=show"}>
            <.icon name="hero-pencil-square" /> Edit ayah
          </.button>
        </:actions>
      </.header>

      <.list>
        <:item title="Ayah ref">{@ayah.ayah_ref}</:item>
        <:item title="Ayah number">{@ayah.ayah_number}</:item>
        <:item title="Text arabic">{@ayah.text_arabic}</:item>
      </.list>
    </Layouts.app>
    """
  end

  @impl true
  def mount(%{"id" => id}, _session, socket) do
    {:ok,
     socket
     |> assign(:page_title, "Show Ayah")
     |> assign(:ayah, Quran.get_ayah!(id))}
  end
end
