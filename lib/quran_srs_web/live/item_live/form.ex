defmodule QuranSrsWeb.ItemLive.Form do
  use QuranSrsWeb, :live_view

  alias QuranSrs.Quran
  alias QuranSrs.Quran.Item

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        {@page_title}
        <:subtitle>Use this form to manage item records in your database.</:subtitle>
      </.header>

      <.form for={@form} id="item-form" phx-change="validate" phx-submit="save">
        <.input field={@form[:item_type]} type="text" label="Item type" />
        <.input field={@form[:title]} type="text" label="Title" />
        <.input field={@form[:start_text]} type="textarea" label="Start text" />
        <.input field={@form[:start_line]} type="number" label="Start line" />
        <.input field={@form[:end_line]} type="number" label="End line" />
        <.input field={@form[:part_number]} type="number" label="Part number" />
        <.input field={@form[:part_title]} type="text" label="Part title" />
        <.input
          field={@form[:tags]}
          type="select"
          multiple
          label="Tags"
          options={[{"Option 1", "option1"}, {"Option 2", "option2"}]}
        />
        <footer>
          <.button phx-disable-with="Saving..." variant="primary">Save Item</.button>
          <.button navigate={return_path(@return_to, @item)}>Cancel</.button>
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
    item = Quran.get_item!(id)

    socket
    |> assign(:page_title, "Edit Item")
    |> assign(:item, item)
    |> assign(:form, to_form(Quran.change_item(item)))
  end

  defp apply_action(socket, :new, _params) do
    item = %Item{}

    socket
    |> assign(:page_title, "New Item")
    |> assign(:item, item)
    |> assign(:form, to_form(Quran.change_item(item)))
  end

  @impl true
  def handle_event("validate", %{"item" => item_params}, socket) do
    changeset = Quran.change_item(socket.assigns.item, item_params)
    {:noreply, assign(socket, form: to_form(changeset, action: :validate))}
  end

  def handle_event("save", %{"item" => item_params}, socket) do
    save_item(socket, socket.assigns.live_action, item_params)
  end

  defp save_item(socket, :edit, item_params) do
    case Quran.update_item(socket.assigns.item, item_params) do
      {:ok, item} ->
        {:noreply,
         socket
         |> put_flash(:info, "Item updated successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, item))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp save_item(socket, :new, item_params) do
    case Quran.create_item(item_params) do
      {:ok, item} ->
        {:noreply,
         socket
         |> put_flash(:info, "Item created successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, item))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp return_path("index", _item), do: ~p"/items"
  defp return_path("show", item), do: ~p"/items/#{item}"
end
