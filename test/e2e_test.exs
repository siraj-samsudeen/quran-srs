defmodule E2ETest do
  use ExUnit.Case, async: false
  use Wallaby.Feature
  import Wallaby.Query

  @moduletag :e2e

  # Helper to build hafiz-related selectors
  # Note: Guard clause must come first to distinguish between name (string) and opts (keyword list)
  defp hafiz_selector(action, opts) when is_list(opts), do: css("button[data-testid^='hafiz-#{action}-']", opts)
  defp hafiz_selector(action, name) when is_binary(name), do: css("button[data-testid='hafiz-#{action}-#{name}']")
  defp hafiz_selector(action, name, opts), do: css("button[data-testid='hafiz-#{action}-#{name}']", opts)

  # Helper to open menu for a hafiz
  defp open_hafiz_menu(session, name) do
    session
    |> click(hafiz_selector("menu", name))
  end

  defp login(session, email \\ "mailsiraj@gmail.com", password \\ "123") do
    session
    |> fill_in(css("input[name='email']"), with: email)
    |> fill_in(css("input[name='password']"), with: password)
    |> click(css("button[type='submit']"))
  end

  defp select_first_hafiz(session) do
    # Click the first hafiz button by data-testid pattern
    session
    |> click(hafiz_selector("switch", at: 0))
  end

  defp create_hafiz(session, name, capacity) do
    session
    |> fill_in(css("input[name='name']"), with: name)
    |> fill_in(css("input[name='daily_capacity']"), with: capacity)
    |> click(css("button", text: "Add Hafiz"))
  end

  defp delete_hafiz(session, name) do
    session
    |> open_hafiz_menu(name)
    |> then(fn session ->
      accept_confirm session, fn session ->
        click(session, hafiz_selector("delete", name))
      end
      session
    end)
  end

  feature "Full Cycle mode is always visible", %{session: session} do
    session
    |> visit("/")
    |> login()
    |> select_first_hafiz()
    |> assert_has(css("[data-testid='mode-fc']"))
  end

  feature "Hafiz CRUD - Create, Switch, and Delete", %{session: session} do
    # Use timestamp to ensure unique name across test runs
    timestamp = :os.system_time(:millisecond)
    test_hafiz_name = "E2E Test #{timestamp}"

    session
    |> visit("/")
    |> login()
    # Now on hafiz selection page

    # Step 1: Create new test hafiz with unique name
    |> create_hafiz(test_hafiz_name, "3")

    # Step 2: Verify the new hafiz button appears (not "Go Back" since we haven't switched yet)
    |> assert_has(hafiz_selector("switch", test_hafiz_name, text: test_hafiz_name))

    # Step 3: Switch to the newly created hafiz using its unique data-testid
    |> click(hafiz_selector("switch", test_hafiz_name))

    # Step 4: Verify we're on home page (System Date and Close Date button are always visible)
    |> assert_has(css("span", text: "System Date:"))
    |> assert_has(css("button", text: "Close Date"))

    # Step 5: Return to hafiz selection page
    |> visit("/users/hafiz_selection")

    # Step 6: Verify current hafiz shows "Go Back to [name]" button
    |> assert_has(hafiz_selector("switch", test_hafiz_name, text: "← Go Back to #{test_hafiz_name}"))

    # Step 7: Verify menu button is NOT present for current hafiz (no delete option)
    |> refute_has(hafiz_selector("menu", test_hafiz_name))

    # Step 8: Switch to a different hafiz so we can delete the test hafiz
    # Click any hafiz button that is NOT the test hafiz (using :not selector)
    |> click(css("button[data-testid^='hafiz-switch-']:not([data-testid='hafiz-switch-#{test_hafiz_name}'])", at: 0))

    # Step 9: Return to hafiz selection page
    |> visit("/users/hafiz_selection")

    # Step 10: Now menu button should be visible for test hafiz (can be deleted)
    |> assert_has(hafiz_selector("menu", test_hafiz_name))

    # Step 11: Delete the test hafiz (opens menu, clicks delete, confirms dialog)
    # Note: delete_hafiz helper opens the dropdown menu first, then clicks delete
    |> delete_hafiz(test_hafiz_name)

    # Step 12: Verify test hafiz button is completely deleted
    |> refute_has(hafiz_selector("switch", test_hafiz_name))

    # Step 13: Verify we're still on hafiz selection page with other hafizs
    |> assert_has(hafiz_selector("switch", minimum: 1))
  end
end
