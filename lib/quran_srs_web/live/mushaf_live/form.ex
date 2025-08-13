defmodule QuranSrsWeb.MushafLive.Form do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran
  alias QuranSrs.Quran.Mushaf

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        {@page_title}
        <:subtitle>Use this form to manage mushaf records in your database.</:subtitle>
      </.header>

      <.form for={@form} id="mushaf-form" phx-change="validate" phx-submit="save">
        <.input field={@form[:name]} type="text" label="Name" />
        <.input field={@form[:description]} type="textarea" label="Description" />
        <footer>
          <.button phx-disable-with="Saving..." variant="primary">Save Mushaf</.button>
          <.button navigate={return_path(@return_to, @mushaf)}>Cancel</.button>
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
    mushaf = Quran.get_mushaf!(id)

    socket
    |> assign(:page_title, "Edit Mushaf")
    |> assign(:mushaf, mushaf)
    |> assign(:form, to_form(Quran.change_mushaf(mushaf)))
  end

  defp apply_action(socket, :new, _params) do
    mushaf = %Mushaf{}

    socket
    |> assign(:page_title, "New Mushaf")
    |> assign(:mushaf, mushaf)
    |> assign(:form, to_form(Quran.change_mushaf(mushaf)))
  end

  @impl true
  def handle_event("validate", %{"mushaf" => mushaf_params}, socket) do
    changeset = Quran.change_mushaf(socket.assigns.mushaf, mushaf_params)
    {:noreply, assign(socket, form: to_form(changeset, action: :validate))}
  end

  def handle_event("save", %{"mushaf" => mushaf_params}, socket) do
    save_mushaf(socket, socket.assigns.live_action, mushaf_params)
  end

  defp save_mushaf(socket, :edit, mushaf_params) do
    case Quran.update_mushaf(socket.assigns.mushaf, mushaf_params) do
      {:ok, mushaf} ->
        {:noreply,
         socket
         |> put_flash(:info, "Mushaf updated successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, mushaf))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp save_mushaf(socket, :new, mushaf_params) do
    case Quran.create_mushaf(mushaf_params) do
      {:ok, mushaf} ->
        {:noreply,
         socket
         |> put_flash(:info, "Mushaf created successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, mushaf))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp return_path("index", _mushaf), do: ~p"/mushafs"
  defp return_path("show", mushaf), do: ~p"/mushafs/#{mushaf}"
end
