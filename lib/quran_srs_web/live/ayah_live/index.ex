defmodule QuranSrsWeb.AyahLive.Index do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Listing Ayahs
        <:actions>
          <.button variant="primary" navigate={~p"/ayahs/new"}>
            <.icon name="hero-plus" /> New Ayah
          </.button>
        </:actions>
      </.header>

      <.table
        id="ayahs"
        rows={@streams.ayahs}
        row_click={fn {_id, ayah} -> JS.navigate(~p"/ayahs/#{ayah}") end}
      >
        <:col :let={{_id, ayah}} label="Ayah ref">{ayah.ayah_ref}</:col>
        <:col :let={{_id, ayah}} label="Ayah number">{ayah.ayah_number}</:col>
        <:col :let={{_id, ayah}} label="Text arabic">{ayah.text_arabic}</:col>
        <:action :let={{_id, ayah}}>
          <div class="sr-only">
            <.link navigate={~p"/ayahs/#{ayah}"}>Show</.link>
          </div>
          <.link navigate={~p"/ayahs/#{ayah}/edit"}>Edit</.link>
        </:action>
        <:action :let={{id, ayah}}>
          <.link
            phx-click={JS.push("delete", value: %{id: ayah.id}) |> hide("##{id}")}
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
     |> assign(:page_title, "Listing Ayahs")
     |> stream(:ayahs, Quran.list_ayahs())}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    ayah = Quran.get_ayah!(id)
    {:ok, _} = Quran.delete_ayah(ayah)

    {:noreply, stream_delete(socket, :ayahs, ayah)}
  end
end
