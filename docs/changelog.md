# Changelog
All notable changes to Quran SRS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) 
and [How to Write a Git Commit Message](https://cbea.ms/git-commit/).

---

## [Unreleased]

### Added
- Generate new Phoenix 1.8.0 application
  - using `mix phx.new . --app quran_srs`
  - Used current directory to preserve existing project structure
  - All dependencies installed with `mix deps.get`
  - `mix test` reports all 5 tests passing
  - started server with `mix phx.server` and home page is working
- Generate Phoenix authentication system
  - using `mix phx.gen.auth Accounts User users`
  - Created LiveView-based authentication
  - `mix test` reports all 94 tests passing

