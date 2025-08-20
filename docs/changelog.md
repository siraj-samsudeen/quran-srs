# Changelog
All notable changes to Quran SRS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) 
and [How to Write a Git Commit Message](https://cbea.ms/git-commit/).

---

## [Unreleased]

### Added
- feature: Generate new Phoenix 1.8.0 application
  - using `mix phx.new . --app quran_srs`
  - Used current directory to preserve existing project structure
  - All dependencies installed with `mix deps.get`
  - `mix test` reports all 5 tests passing
  - started server with `mix phx.server` and home page is working
- feature: Generate Phoenix authentication system
  - using `mix phx.gen.auth Accounts User users`
  - Created LiveView-based authentication
  - `mix test` reports all 94 tests passing
- feature: Generate Mushaf CRUD with LiveView
  - using `mix phx.gen.live Quran Mushaf mushafs name description:text --no-scope`
  - Created system-wide master data (no user scoping)
  - Added CRUD routes `/mushafs` to router.ex
  - `mix test` reports all 108 tests passing
- chore: Update Mushaf seed data
  - Added 2 mushafs: Madinah Mushaf and Indo-Pak 15-Line
  - Verified data appears at `/mushafs` route
- feature: Generate Surah CRUD with LiveView
  - using `mix phx.gen.live Quran Surah surahs number:integer name total_ayat:integer --no-scope`
  - Created system-wide master data (no user scoping)
  - Added CRUD routes `/surahs` to router.ex
  - `mix test` reports all 122 tests passing
- chore: Seed Surah master data
  - Moved essential master data (Mushafs, Surahs) to production-safe migrations
  - Organized CSV files in `priv/repo/master_data/` for production reference data
  - Created `20250814055758_seed_master_data.exs` migration
  - Imported all 114 surahs from surahs.csv using Explorer library
  - Verified data appears at `/surahs` route
  - Added smoke test to check master data health
  - Checks mushafs == 2 and surahs == 114 (catches duplicates)
  - Updated `quran_test.exs` tests to work with master data present
- feature: Generate Page CRUD with proper mushaf context and clean architecture
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


