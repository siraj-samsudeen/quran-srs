defmodule QuranSrsWeb.AyahLive.Form do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran
  alias QuranSrs.Quran.Ayah

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        {@page_title}
        <:subtitle>Use this form to manage ayah records in your database.</:subtitle>
      </.header>

      <.form for={@form} id="ayah-form" phx-change="validate" phx-submit="save">
        <.input
          field={@form[:surah_id]}
          type="select"
          label="Surah"
          options={@surah_options}
          prompt="Select a surah"
          help="Select the surah (chapter) this verse belongs to"
        />

        <.input
          field={@form[:ayah_ref]}
          type="text"
          label="Ayah Reference"
          placeholder="2:255"
          help="Format: surah:ayah (e.g. 2:255 for Ayat Al-Kursi)"
        />

        <.input
          field={@form[:ayah_number]}
          type="number"
          label="Ayah Number"
          placeholder="1-286"
          help="Verse number within the selected surah"
        />

        <.input
          field={@form[:text_arabic]}
          type="textarea"
          label="Arabic Text"
          placeholder="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ..."
          rows="4"
        />
        <footer>
          <.button phx-disable-with="Saving..." variant="primary">Save Ayah</.button>
          <.button navigate={return_path(@return_to, @ayah)}>Cancel</.button>
        </footer>
      </.form>
    </Layouts.app>
    """
  end

  @impl true
  def mount(params, _session, socket) do
    {:ok,
     socket
     |> assign(:return_to, return_to(params["return_to"]))
     |> apply_action(socket.assigns.live_action, params)}
  end

  defp return_to("show"), do: "show"
  defp return_to(_), do: "index"

  defp apply_action(socket, :edit, %{"id" => id}) do
    ayah = Quran.get_ayah!(id)

    socket
    |> assign(:page_title, "Edit Ayah")
    |> assign(:ayah, ayah)
    |> assign(:form, to_form(Quran.change_ayah(ayah)))
    |> assign(:surah_options, Quran.list_surah_options())
  end

  defp apply_action(socket, :new, _params) do
    ayah = %Ayah{}

    socket
    |> assign(:page_title, "New Ayah")
    |> assign(:ayah, ayah)
    |> assign(:form, to_form(Quran.change_ayah(ayah)))
    |> assign(:surah_options, Quran.list_surah_options())
  end

  @impl true
  def handle_event("validate", %{"ayah" => ayah_params}, socket) do
    changeset = Quran.change_ayah(socket.assigns.ayah, ayah_params)
    {:noreply, assign(socket, form: to_form(changeset, action: :validate))}
  end

  def handle_event("save", %{"ayah" => ayah_params}, socket) do
    save_ayah(socket, socket.assigns.live_action, ayah_params)
  end

  defp save_ayah(socket, :edit, ayah_params) do
    case Quran.update_ayah(socket.assigns.ayah, ayah_params) do
      {:ok, ayah} ->
        {:noreply,
         socket
         |> put_flash(:info, "Ayah updated successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, ayah))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp save_ayah(socket, :new, ayah_params) do
    case Quran.create_ayah(ayah_params) do
      {:ok, ayah} ->
        {:noreply,
         socket
         |> put_flash(:info, "Ayah created successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, ayah))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp return_path("index", _ayah), do: ~p"/ayahs"
  defp return_path("show", ayah), do: ~p"/ayahs/#{ayah}"
end
