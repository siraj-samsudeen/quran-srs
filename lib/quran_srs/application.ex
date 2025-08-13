defmodule QuranSrs.Application do
  # See https://hexdocs.pm/elixir/Application.html
  # for more information on OTP Applications
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    children = [
      QuranSrsWeb.Telemetry,
      QuranSrs.Repo,
      {DNSCluster, query: Application.get_env(:quran_srs, :dns_cluster_query) || :ignore},
      {Phoenix.PubSub, name: QuranSrs.PubSub},
      # Start a worker by calling: QuranSrs.Worker.start_link(arg)
      # {QuranSrs.Worker, arg},
      # Start to serve requests, typically the last entry
      QuranSrsWeb.Endpoint
    ]

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: QuranSrs.Supervisor]
    Supervisor.start_link(children, opts)
  end

  # Tell Phoenix to update the endpoint configuration
  # whenever the application is updated.
  @impl true
  def config_change(changed, _new, removed) do
    QuranSrsWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end
