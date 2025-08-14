defmodule QuranSrsWeb.SurahLive.Form do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran
  alias QuranSrs.Quran.Surah

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        {@page_title}
        <:subtitle>Use this form to manage surah records in your database.</:subtitle>
      </.header>

      <.form for={@form} id="surah-form" phx-change="validate" phx-submit="save">
        <.input field={@form[:number]} type="number" label="Number" />
        <.input field={@form[:name]} type="text" label="Name" />
        <.input field={@form[:total_ayat]} type="number" label="Total ayat" />
        <footer>
          <.button phx-disable-with="Saving..." variant="primary">Save Surah</.button>
          <.button navigate={return_path(@return_to, @surah)}>Cancel</.button>
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
    surah = Quran.get_surah!(id)

    socket
    |> assign(:page_title, "Edit Surah")
    |> assign(:surah, surah)
    |> assign(:form, to_form(Quran.change_surah(surah)))
  end

  defp apply_action(socket, :new, _params) do
    surah = %Surah{}

    socket
    |> assign(:page_title, "New Surah")
    |> assign(:surah, surah)
    |> assign(:form, to_form(Quran.change_surah(surah)))
  end

  @impl true
  def handle_event("validate", %{"surah" => surah_params}, socket) do
    changeset = Quran.change_surah(socket.assigns.surah, surah_params)
    {:noreply, assign(socket, form: to_form(changeset, action: :validate))}
  end

  def handle_event("save", %{"surah" => surah_params}, socket) do
    save_surah(socket, socket.assigns.live_action, surah_params)
  end

  defp save_surah(socket, :edit, surah_params) do
    case Quran.update_surah(socket.assigns.surah, surah_params) do
      {:ok, surah} ->
        {:noreply,
         socket
         |> put_flash(:info, "Surah updated successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, surah))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp save_surah(socket, :new, surah_params) do
    case Quran.create_surah(surah_params) do
      {:ok, surah} ->
        {:noreply,
         socket
         |> put_flash(:info, "Surah created successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, surah))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp return_path("index", _surah), do: ~p"/surahs"
  defp return_path("show", surah), do: ~p"/surahs/#{surah}"
end
