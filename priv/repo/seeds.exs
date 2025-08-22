# Development seeds file
# Run with: mix run priv/repo/seeds.exs
#
# Master data (mushafs, surahs, pages, items) is loaded via migrations.
# See: priv/repo/migrations/*_seed_master_data.exs
#
# This file is reserved for development convenience data like:
# - Sample user accounts
# - Demo hafiz profiles
# - Test memorization progress
# - Sample revision history

# Development seed data only - don't run in test environment
unless Mix.env() == :test do
  alias QuranSrs.{Quran, Accounts}

  IO.puts("🌱 Development seeds - Creating demo user and items to showcase different types")

  # Create demo user for custom items
  {:ok, demo_user} = Accounts.register_user(%{
    email: "demo@example.com",
    password: "demouserpassword123"
  })

  IO.puts("✓ Created demo user: #{demo_user.email}")

  # Mutashabihat items - Similar verses that are often confused
  mutashabihat_items = [
    # Lut (AS) story - appears in multiple surahs with similar wording
    %{
      item_type: "ayah_range",
      title: "Lut (AS) Story - Al-A'raf 7:80-84",
      start_text: "Wa Lutan idh",
      part_title: "First detailed account - includes punishment details",
      tags: ["mutashabihat", "prophets", "lut", "cross_surah"],
      surah_id: 7,  # Al-A'raf
      page_id: 168  # Same page (5 verses)
    },

    %{
      item_type: "ayah_range",
      title: "Lut (AS) Story - Hud 11:77-83",
      start_text: "Wa lamma ja'at",
      part_title: "Angels visit - includes dialogue with angels",
      tags: ["mutashabihat", "prophets", "lut", "cross_surah"],
      surah_id: 11, # Hud
      page_id: 235, # Approximate page in Madinah Mushaf
      end_page_id: 236  # Spans to next page (7 verses)
    },

    %{
      item_type: "ayah_range",
      title: "Lut (AS) Story - Al-Hijr 15:57-77",
      start_text: "Qala fa ma",
      part_title: "Longest version - most detailed dialogue",
      tags: ["mutashabihat", "prophets", "lut", "cross_surah"],
      surah_id: 15, # Al-Hijr
      page_id: 267, # Approximate page in Madinah Mushaf
      end_page_id: 268  # Spans multiple pages (21 verses)
    },

    # Destroyed nations - different surahs, similar openings
    %{
      item_type: "ayah_range",
      title: "Destroyed Nations - Qaf 50:12-14",
      start_text: "Kadhdhabat qablahum",
      part_title: "Creation context - mentions multiple nations",
      tags: ["mutashabihat", "destroyed_nations"],
      surah_id: 50, # Qaf
      page_id: 519  # Same page (3 verses)
    },

    %{
      item_type: "ayah_range",
      title: "Destroyed Nations - Sad 38:12-14",
      start_text: "Kadhdhabat qablahum",
      part_title: "Dawud context - different nation order",
      tags: ["mutashabihat", "destroyed_nations"],
      surah_id: 38, # Sad
      page_id: 453  # Same page (3 verses)
    },

    # Inheritance laws - same surah but confusing
    %{
      item_type: "ayah_range",
      title: "Inheritance Laws - Nisa 4:11-12",
      start_text: "Yooseekumu Allahu fee",
      part_title: "Main inheritance law - children and parents",
      tags: ["mutashabihat", "inheritance"],
      surah_id: 4,  # An-Nisa
      page_id: 78   # Same page (2 verses)
    },

    %{
      item_type: "ayah_range",
      title: "Inheritance Laws - Nisa 4:176",
      start_text: "Yastaftoonaka quli",
      part_title: "Last verse of Nisa - also about inheritance (Kalaalah)",
      tags: ["mutashabihat", "inheritance"],
      surah_id: 4,  # An-Nisa
      page_id: 106  # Same page (single verse)
    }
  ]

  # Custom items created by demo user - Page 106 divided into 4 parts
  custom_items = [
    # Page 106 Part 1 - Nisa End
    %{
      item_type: "partial_page",
      title: "Page 106 Part 1 - Nisa End",
      start_text: "Wa in khaaftum",
      start_line: 1,
      end_line: 4,
      part_number: 1,
      part_title: "Marriage and family guidance",
      tags: ["partial_page", "custom"],
      created_by_id: demo_user.id
    },

    # Page 106 Part 2 - Transition
    %{
      item_type: "partial_page",
      title: "Page 106 Part 2 - Nisa Conclusion",
      start_text: "Wa lillahi ma",
      start_line: 5,
      end_line: 8,
      part_number: 2,
      part_title: "Allah's dominion over heavens and earth",
      tags: ["partial_page", "custom"],
      created_by_id: demo_user.id
    },

    # Page 106 Part 3 - Maidah Start
    %{
      item_type: "partial_page",
      title: "Page 106 Part 3 - Maidah Start",
      start_text: "Ya ayyuha allatheena",
      start_line: 9,
      end_line: 12,
      part_number: 3,
      part_title: "Contracts and obligations",
      tags: ["partial_page", "custom"],
      created_by_id: demo_user.id
    },

    # Page 106 Part 4 - Maidah Continues
    %{
      item_type: "partial_page",
      title: "Page 106 Part 4 - Maidah Laws",
      start_text: "Uhillat lakum",
      start_line: 13,
      end_line: 15,
      part_number: 4,
      part_title: "Permissible animals and hunting laws",
      tags: ["partial_page", "custom"],
      created_by_id: demo_user.id
    }
  ]

  demo_items = mutashabihat_items ++ custom_items

  # Insert demo items showcasing different memorization unit types
  Enum.each(demo_items, fn attrs ->
    case Quran.create_item(attrs) do
      {:ok, item} -> IO.puts("✓ Created demo item: #{item.title}")
      {:error, changeset} -> IO.puts("✗ Failed to create item: #{inspect(changeset.errors)}")
    end
  end)

  IO.puts("✓ Seeds complete - #{length(demo_items)} demo items created showing different types")
  IO.puts("  • Mutashabihat: #{length(mutashabihat_items)} similar verses")
  IO.puts("  • Custom items: #{length(custom_items)} user-created partial pages (Page 106 in 4 parts)")
end
