# Script for populating the database. You can run it as:
#
#     mix run priv/repo/seeds.exs
#
# Inside the script, you can read and write to any of your
# repositories directly:
#
#     QuranSrs.Repo.insert!(%QuranSrs.SomeSchema{})
#
# We recommend using the bang functions (`insert!`, `update!`
# and so on) as they will fail if something goes wrong.

# Seed Mushafs
alias QuranSrs.Quran

# Madinah Mushaf - Primary mushaf from production system
{:ok, _madinah_mushaf} = Quran.create_mushaf(%{
  name: "Madinah Mushaf",
  description: "Standard Madinah Mushaf with 604 pages"
})

# Indian/Pakistani Mushaf - 15-line format
{:ok, _indo_pak_mushaf} = Quran.create_mushaf(%{
  name: "Indo-Pak 15-Line",
  description: "Indian/Pakistani Mushaf with 15 lines per page"
})

IO.puts("Seeded Mushafs")
