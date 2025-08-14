defmodule QuranSrs.MasterDataHealthTest do
  use QuranSrs.DataCase
  alias QuranSrs.Quran

  describe "master data health check" do
    test "essential master data is present in both dev and test" do
      # Verify exact counts (catches duplicates from running migrations twice)
      assert Quran.list_mushafs() |> length() == 2
      assert Quran.list_surahs() |> length() == 114
    end
  end
end
