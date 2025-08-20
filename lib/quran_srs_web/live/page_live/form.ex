defmodule QuranSrsWeb.PageLive.Form do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran
  alias QuranSrs.Quran.Page

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        {@page_title}
        <:subtitle>Use this form to manage page records in your database.</:subtitle>
      </.header>

      <.form for={@form} id="page-form" phx-change="validate" phx-submit="save">
        <.input field={@form[:page_number]} type="number" label="Page number" />
        <.input field={@form[:juz_number]} type="number" label="Juz number" />
        <.input field={@form[:start_text]} type="textarea" label="Start text" />
        <.input field={@form[:mushaf_id]} type="select" label="Mushaf" options={@mushaf_options} />
        <footer>
          <.button phx-disable-with="Saving..." variant="primary">Save Page</.button>
          <.button navigate={return_path(@return_to, @page, @current_mushaf)}>Cancel</.button>
        </footer>
      </.form>
    </Layouts.app>
    """
  end

  @impl true
  def mount(params, _session, socket) do
    mushaf_id = String.to_integer(params["mushaf_id"])
    mushaf = Quran.get_mushaf!(mushaf_id)
    mushafs = Quran.list_mushafs()
    mushaf_options = Enum.map(mushafs, &{&1.name, &1.id})

    {:ok,
     socket
     |> assign(:return_to, return_to(params["return_to"]))
     |> assign(:current_mushaf, mushaf)
     |> assign(:mushaf_options, mushaf_options)
     |> apply_action(socket.assigns.live_action, params)}
  end

  defp return_to("show"), do: "show"
  defp return_to(_), do: "index"

  defp apply_action(socket, :edit, %{"id" => id}) do
    page = Quran.get_page!(id)

    socket
    |> assign(:page_title, "Edit Page")
    |> assign(:page, page)
    |> assign(:form, to_form(Quran.change_page(page)))
  end

  defp apply_action(socket, :new, _params) do
    page = %Page{mushaf_id: socket.assigns.current_mushaf.id}

    socket
    |> assign(:page_title, "New Page - #{socket.assigns.current_mushaf.name}")
    |> assign(:page, page)
    |> assign(:form, to_form(Quran.change_page(page)))
  end

  @impl true
  def handle_event("validate", %{"page" => page_params}, socket) do
    changeset = Quran.change_page(socket.assigns.page, page_params)
    {:noreply, assign(socket, form: to_form(changeset, action: :validate))}
  end

  def handle_event("save", %{"page" => page_params}, socket) do
    save_page(socket, socket.assigns.live_action, page_params)
  end

  defp save_page(socket, :edit, page_params) do
    case Quran.update_page(socket.assigns.page, page_params) do
      {:ok, page} ->
        {:noreply,
         socket
         |> put_flash(:info, "Page updated successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, page, socket.assigns.current_mushaf))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp save_page(socket, :new, page_params) do
    case Quran.create_page(page_params) do
      {:ok, page} ->
        {:noreply,
         socket
         |> put_flash(:info, "Page created successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, page, socket.assigns.current_mushaf))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp return_path("index", _page, mushaf), do: ~p"/mushafs/#{mushaf}/pages"
  defp return_path("show", page, mushaf), do: ~p"/mushafs/#{mushaf}/pages/#{page}"
end
