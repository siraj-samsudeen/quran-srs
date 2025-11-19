defmodule QuranSrsWeb.PageController do
  use QuranSrsWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end
