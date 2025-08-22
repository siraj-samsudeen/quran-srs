# Git Commit Log

refactor: Consolidate all master data into single migration
  - Merged 4 separate migrations into single create_master_data.exs
  - Updated seed_master_data.exs migration to insert Item masterdata

chore: prepare item master data from prod
  - Took the item data for page, partial_page and surah items - 836 items
  - Title for pages where partial_pages exist like Page 106 still carries generic title `Item 106` FIXLATER

refactor: Consolidate master data into clean 2-file structure
  - Single migration for all master data schema creation
  - Single migration for seeding all master data from CSV
  - Added 836 items from production database to master data

feature: Generate Item CRUD
  - using `mix phx.gen.live` as per data model

feature: Add help text support to input components
  - Added `help` attribute to core input component
  - Displays helpful guidance below input fields
  - Applied to all input types (text, select, textarea)
  - Updated Ayah form with helpful examples and format guidance
  - Help text shows in gray, errors show below in red (no conflict)

fix: Complete Ayah FK handling for Surah relationship
  - Fixed schema: changed `field :surah_id, :id` to `belongs_to :surah, Surah`
  - Updated changeset to include surah_id in cast and validate_required
  - Added preloading to list_ayahs/0 and get_ayah!/1 context functions
  - Created list_surah_options/0 helper for dropdown (shows "1. Al-Fatihah" format)
  - Updated LiveView form to include surah select dropdown
  - Fixed LiveView index to display surah name instead of ID
  - Updated LiveView show to display surah details
  - Fixed test fixtures to create surah and include surah_id
  - Updated test assertions to handle preloaded associations (can't use == comparison)
  - Documented Phoenix FK fix pattern in CLAUDE.md for future generators

feature: Generate Ayah CRUD
  - using `mix phx.gen.live Quran Ayah ayahs ayah_ref:unique ayah_number:integer text_arabic:text surah_id:references:surahs --no-scope`
  - this does NOT create the FK fields properly and liveviews do not have a way to select the FK field

feature: Generate Page CRUD with proper mushaf context and clean architecture
  - Generated initial page CRUD: `mix phx.gen.live MasterData Page pages page_number:integer juz_number:integer start_text:text mushaf_id:references:mushafs --no-scope`
  - Created proper Ecto associations: Page belongs_to Mushaf, Mushaf has_many Pages
  - Updated context `quran.ex` to add `list_pages_by_mushaf`
  - Updated router to nest page routes under mushaf: `/mushafs/:mushaf_id/pages`
  - Modified all LiveView modules to accept and use mushaf_id parameter from URL
  - Added pages.csv to `priv/repo/master_data/` (604 pages for Madinah Mushaf)
  - Consolidated page schema into existing `create_mushafs.exs` migration (logical grouping)
  - Consolidated page seeding into existing `seed_master_data.exs` migration (proper dependency order)
  - Added check pages == 604 to master data health check
  - `mix test` reports all 137 tests

chore: Seed Surah master data
  - Moved essential master data (Mushafs, Surahs) to production-safe migrations
  - Organized CSV files in `priv/repo/master_data/` for production reference data
  - Created `20250814055758_seed_master_data.exs` migration
  - Imported all 114 surahs from surahs.csv using Explorer library
  - Verified data appears at `/surahs` route
  - Added smoke test to check master data health
  - Checks mushafs == 2 and surahs == 114 (catches duplicates)
  - Updated `quran_test.exs` tests to work with master data present

feature: Generate Surah CRUD with LiveView
  - using `mix phx.gen.live Quran Surah surahs number:integer name total_ayat:integer --no-scope`
  - Created system-wide master data (no user scoping)
  - Added CRUD routes `/surahs` to router.ex
  - `mix test` reports all 122 tests passing

chore: Update Mushaf seed data
  - Added 2 mushafs: Madinah Mushaf and Indo-Pak 15-Line
  - Verified data appears at `/mushafs` route

feature: Generate Mushaf CRUD with LiveView
  - using `mix phx.gen.live Quran Mushaf mushafs name description:text --no-scope`
  - Created system-wide master data (no user scoping)
  - Added CRUD routes `/mushafs` to router.ex
  - `mix test` reports all 108 tests passing

feature: Generate Phoenix authentication system
  - using `mix phx.gen.auth Accounts User users`
  - Created LiveView-based authentication
  - `mix test` reports all 94 tests passing

feature: Generate new Phoenix 1.8.0 application
  - using `mix phx.new . --app quran_srs`
  - Used current directory to preserve existing project structure
  - All dependencies installed with `mix deps.get`
  - `mix test` reports all 5 tests passing
  - started server with `mix phx.server` and home page is working

feature: Generate Phoenix authentication system
  - using `mix phx.gen.auth Accounts User users`
  - Created LiveView-based authentication
  - `mix test` reports all 94 tests passing

feature: Generate Mushaf CRUD with LiveView
  - using `mix phx.gen.live Quran Mushaf mushafs name description:text --no-scope`
  - Created system-wide master data (no user scoping)
  - Added CRUD routes `/mushafs` to router.ex
  - `mix test` reports all 108 tests passing
chore: Update Mushaf seed data
  - Added 2 mushafs: Madinah Mushaf and Indo-Pak 15-Line
  - Verified data appears at `/mushafs` route

feature: Generate Surah CRUD with LiveView
  - using `mix phx.gen.live Quran Surah surahs number:integer name total_ayat:integer --no-scope`
  - Created system-wide master data (no user scoping)
  - Added CRUD routes `/surahs` to router.ex
  - `mix test` reports all 122 tests passing

chore: Seed Surah master data
  - Moved essential master data (Mushafs, Surahs) to production-safe migrations
  - Organized CSV files in `priv/repo/master_data/` for production reference data
  - Created `20250814055758_seed_master_data.exs` migration
  - Imported all 114 surahs from surahs.csv using Explorer library
  - Verified data appears at `/surahs` route
  - Added smoke test to check master data health
  - Checks mushafs == 2 and surahs == 114 (catches duplicates)
  - Updated `quran_test.exs` tests to work with master data present

feature: Generate Page CRUD with proper mushaf context and clean architecture
  - Generated initial page CRUD: `mix phx.gen.live MasterData Page pages page_number:integer juz_number:integer start_text:text mushaf_id:references:mushafs --no-scope`
  - Created proper Ecto associations: Page belongs_to Mushaf, Mushaf has_many Pages
  - Updated context `quran.ex` to add `list_pages_by_mushaf`
  - Updated router to nest page routes under mushaf: `/mushafs/:mushaf_id/pages`
  - Modified all LiveView modules to accept and use mushaf_id parameter from URL
  - Added pages.csv to `priv/repo/master_data/` (604 pages for Madinah Mushaf)
  - Consolidated page schema into existing `create_mushafs.exs` migration (logical grouping)
  - Consolidated page seeding into existing `seed_master_data.exs` migration (proper dependency order)
  - Added check pages == 604 to master data health check
  - `mix test` reports all 137 tests

feature: Generate Ayah CRUD
  - using `mix phx.gen.live Quran Ayah ayahs ayah_ref:unique ayah_number:integer text_arabic:text surah_id:references:surahs --no-scope`
  - this does NOT create the FK fields properly and liveviews do not have a way to select the FK field

fix: Complete Ayah FK handling for Surah relationship
  - Fixed schema: changed `field :surah_id, :id` to `belongs_to :surah, Surah`
  - Updated changeset to include surah_id in cast and validate_required
  - Added preloading to list_ayahs/0 and get_ayah!/1 context functions
  - Created list_surah_options/0 helper for dropdown (shows "1. Al-Fatihah" format)
  - Updated LiveView form to include surah select dropdown
  - Fixed LiveView index to display surah name instead of ID
  - Updated LiveView show to display surah details
  - Fixed test fixtures to create surah and include surah_id
  - Updated test assertions to handle preloaded associations (can't use == comparison)
  - Documented Phoenix FK fix pattern in CLAUDE.md for future generators

feature: Add help text support to input components
  - Added `help` attribute to core input component
  - Displays helpful guidance below input fields
  - Applied to all input types (text, select, textarea)
  - Updated Ayah form with helpful examples and format guidance
  - Help text shows in gray, errors show below in red (no conflict)

feature: Generate Item CRUD
  - using `mix phx.gen.live` as per data model

refactor: Consolidate master data into clean 2-file structure
  - Single migration for all master data schema creation
  - Single migration for seeding all master data from CSV
  - Added 836 items from production database to master data

