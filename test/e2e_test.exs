defmodule E2ETest do
  use ExUnit.Case, async: false
  use Wallaby.Feature
  import Wallaby.Query

  @moduletag :e2e

  # Database path for FastHTML app
  @db_path "../quran-srs/data/quran_v10.db"

  # Helper to build hafiz-related selectors
  # Note: Guard clause must come first to distinguish between name (string) and opts (keyword list)
  defp hafiz_selector(action, opts) when is_list(opts), do: css("button[data-testid^='hafiz-#{action}-']", opts)
  defp hafiz_selector(action, name) when is_binary(name), do: css("button[data-testid='hafiz-#{action}-#{name}']")
  defp hafiz_selector(action, name, opts), do: css("button[data-testid='hafiz-#{action}-#{name}']", opts)

  # Database helper functions
  defp query(sql) do
    :os.cmd(~c"sqlite3 #{@db_path} \"#{sql}\"") |> to_string()
  end

  defp get_hafiz_id_by_name(name) do
    result = query("SELECT id FROM hafizs WHERE name = '#{name}';")
    result |> String.trim() |> String.to_integer()
  end

  defp get_available_item_id(hafiz_id) do
    # Get first unmemorized item for this hafiz
    result = query("SELECT item_id FROM hafizs_items WHERE hafiz_id = #{hafiz_id} AND memorized = 0 LIMIT 1;")
    case String.trim(result) do
      "" -> 1  # Default to item 1 if none found
      id -> String.to_integer(id)
    end
  end

  defp seed_item_in_mode(hafiz_id, item_id, mode_code, opts \\ %{}) do
    memorized = Map.get(opts, :memorized, true)
    next_review = Map.get(opts, :next_review, "2025-11-07")
    next_interval = Map.get(opts, :next_interval, "NULL")
    bad_streak = Map.get(opts, :bad_streak, 0)
    last_review = Map.get(opts, :last_review, "NULL")

    last_review_str = if last_review == "NULL", do: "NULL", else: "'#{last_review}'"
    next_interval_str = if next_interval == "NULL", do: "NULL", else: "#{next_interval}"

    # Check if item already exists for this hafiz
    existing = query("SELECT COUNT(*) FROM hafizs_items WHERE hafiz_id = #{hafiz_id} AND item_id = #{item_id};")

    if String.trim(existing) == "0" do
      # Insert new item
      query("""
      INSERT INTO hafizs_items (hafiz_id, item_id, mode_code, memorized, next_review, next_interval, bad_streak, last_review, page_number)
      SELECT #{hafiz_id}, #{item_id}, '#{mode_code}', #{if memorized, do: 1, else: 0}, '#{next_review}', #{next_interval_str}, #{bad_streak}, #{last_review_str}, items.page_id
      FROM items WHERE items.id = #{item_id};
      """)
    else
      # Update existing item
      query("""
      UPDATE hafizs_items
      SET mode_code = '#{mode_code}',
          memorized = #{if memorized, do: 1, else: 0},
          next_review = '#{next_review}',
          next_interval = #{next_interval_str},
          bad_streak = #{bad_streak},
          last_review = #{last_review_str}
      WHERE hafiz_id = #{hafiz_id} AND item_id = #{item_id};
      """)
    end
  end

  defp seed_revision(hafiz_id, item_id, mode_code, revision_date, rating) do
    query("""
    INSERT INTO revisions (hafiz_id, item_id, mode_code, revision_date, rating)
    VALUES (#{hafiz_id}, #{item_id}, '#{mode_code}', '#{revision_date}', #{rating});
    """)
  end

  defp set_hafiz_date(hafiz_id, date_string) when is_integer(hafiz_id) do
    query("UPDATE hafizs SET current_date = '#{date_string}' WHERE id = #{hafiz_id};")
  end

  defp assert_item_in_mode(hafiz_id, item_id, expected_mode) do
    result = query("SELECT mode_code FROM hafizs_items WHERE hafiz_id = #{hafiz_id} AND item_id = #{item_id};")
    actual_mode = String.trim(result)
    assert actual_mode == expected_mode, "Expected item #{item_id} to be in mode #{expected_mode}, but found #{actual_mode}"
  end

  defp get_hafizs_items_from_db(hafiz_id, item_id) do
    result = query("SELECT mode_code, bad_streak, next_interval, memorized FROM hafizs_items WHERE hafiz_id = #{hafiz_id} AND item_id = #{item_id};")
    [mode_code, bad_streak, next_interval, memorized] = result |> String.trim() |> String.split("|")
    %{
      mode_code: mode_code,
      bad_streak: String.to_integer(bad_streak || "0"),
      next_interval: if(next_interval == "", do: nil, else: String.to_integer(next_interval)),
      memorized: memorized == "1"
    }
  end

  defp assert_revision_exists(hafiz_id, item_id, mode_code, revision_date, rating) do
    result = query("SELECT COUNT(*) FROM revisions WHERE hafiz_id = #{hafiz_id} AND item_id = #{item_id} AND mode_code = '#{mode_code}' AND revision_date = '#{revision_date}' AND rating = #{rating};")
    count = result |> String.trim() |> String.to_integer()
    assert count > 0, "Expected revision to exist for item #{item_id} on #{revision_date} with rating #{rating}, but none found"
  end

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

  defp create_test_hafiz_and_switch(session, name_suffix \\ nil) do
    timestamp = :os.system_time(:millisecond)
    test_hafiz_name = if name_suffix, do: "E2E #{name_suffix} #{timestamp}", else: "E2E Test #{timestamp}"

    session
    |> visit("/")
    |> login()
    |> create_hafiz(test_hafiz_name, "20")
    |> click(hafiz_selector("switch", test_hafiz_name))

    {session, test_hafiz_name}
  end

  defp cleanup_test_hafiz(session, hafiz_name) do
    session
    |> visit("/users/hafiz_selection")
    |> then(fn session ->
      # Switch to a different hafiz first so we can delete the test hafiz
      session
      |> click(css("button[data-testid^='hafiz-switch-']:not([data-testid='hafiz-switch-#{hafiz_name}'])", at: 0))
      |> visit("/users/hafiz_selection")
      |> delete_hafiz(hafiz_name)
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

  feature "Full Cycle - Review item due today", %{session: session} do
    {session, test_hafiz_name} = create_test_hafiz_and_switch(session, "FC Review")
    hafiz_id = get_hafiz_id_by_name(test_hafiz_name)
    item_id = 1
    current_date = "2025-11-07"

    # Set current date first (before seeding)
    set_hafiz_date(hafiz_id, current_date)

    # Seed: Item in FC mode, due today
    seed_item_in_mode(hafiz_id, item_id, "FC", %{
      memorized: true,
      next_review: current_date,
      last_review: "NULL"
    })

    # Test
    session =
      session
      |> visit("/")
      |> assert_has(css("[data-testid='mode-fc']"))
      |> assert_has(css("select[data-testid='rating-#{item_id}']"))

    # Select "Good" rating by clicking the option
    # We need to use execute_script to change the value and trigger the change event
    session =
      session
      |> execute_script("document.querySelector('select[data-testid=\"rating-#{item_id}\"]').value = '1'")
      |> execute_script("document.querySelector('select[data-testid=\"rating-#{item_id}\"]').dispatchEvent(new Event('change'))")

    # Give HTMX time to process
    Process.sleep(2000)

    # Verify revision was created
    assert_revision_exists(hafiz_id, item_id, "FC", current_date, 1)

    # Cleanup
    cleanup_test_hafiz(session, test_hafiz_name)
  end
end
