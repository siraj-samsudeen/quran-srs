import { test, expect, Page } from "@playwright/test";

interface WatchlistPage {
  pageNumber: string;
  title: string;
  rowId: string;
  hasCheckbox: boolean;
  isCompleted: boolean;
}

test.describe("Watchlist Workflow E2E Tests", () => {
  const testEmail = "mailsiraj@gmail.com";
  const testPassword = "123";
  const testHafizName = "Siraj";

  // Log in and select hafiz user
  async function loginAndSelectHafiz(page: Page): Promise<void> {
    await page.goto("/users/login");
    await page.getByRole("textbox", { name: "Email" }).fill(testEmail);
    await page.getByRole("textbox", { name: "Password" }).fill(testPassword);
    await page.getByRole("button", { name: "Login" }).click();
    await page.getByTestId(`switch-${testHafizName}-hafiz-button`).click();
    await page.waitForLoadState("networkidle");
  }

  // Get all ungraduated pages
  async function getUngraduatedWatchlistPages(page: Page): Promise<WatchlistPage[]> {
    const pages: WatchlistPage[] = [];
    const rows = await page.locator("tbody tr").all();

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const pageNumber = (await row.locator("td:first-child").textContent())?.trim() || "";
      const title = (await row.locator("td:nth-child(2)").textContent())?.trim() || "";
      const rowId = (await row.getAttribute("id")) || `row-${i}`;

      const hasCheckbox = (await row.locator("input.uk-checkbox").count()) > 0;
      const graduateCheckbox = row.locator("input[id^='graduate-btn-']");
      const isCompleted = (await graduateCheckbox.count()) > 0 && (await graduateCheckbox.isChecked());

      // Only add pages that are not completed
      if (!isCompleted) {
        pages.push({ pageNumber, title, rowId, hasCheckbox, isCompleted });
      }
    }
    return pages;
  }

  // Tick (check) the checkbox on a given watchlist page
  async function tickWatchlistPage(page: Page, watchPage: WatchlistPage): Promise<void> {
    if (!watchPage.hasCheckbox) {
      throw new Error(`Page ${watchPage.pageNumber} has no checkbox to tick`);
    }
    const row = page.locator(`#${watchPage.rowId}`);
    const checkbox = row.locator("input.uk-checkbox");
    await checkbox.check();
    await expect(checkbox).toBeChecked();
  }

  // Verify the page appears checked in the Home watchlist after ticking
  async function verifyPageInHomeWatchlist(page: Page, watchPage: WatchlistPage): Promise<void> {
    await page.getByRole("link", { name: "Home" }).click();
    await expect(page).toHaveURL("/");

    await page.getByRole("button", { name: /Weekly Reps/ }).click();

    const link = page.locator(`[data-testid="watch_list_tbody"] a`, { hasText: watchPage.pageNumber });
    await expect(link).toBeVisible();

    const row = link.locator('xpath=ancestor::tr');
    const checkbox = row.locator('input[type="checkbox"].uk-checkbox.watch_list_ids');
    await expect(checkbox).toBeChecked();
  }

  // Run before each test: login and go to watchlist page
  test.beforeEach(async ({ page }) => {
    await loginAndSelectHafiz(page);
    await page.goto("/watch_list/");
  });

  // Test 1: Verify all ungraduated pages have correct checkbox or tick mark
  test("verify all ungraduated pages have correct checkbox/✅ state", async ({ page }) => {
    const pages = await getUngraduatedWatchlistPages(page);
    expect(pages.length).toBeGreaterThan(0);

    for (const p of pages) {
      const row = page.locator(`#${p.rowId}`);

      if (p.hasCheckbox) {
        const checkbox = row.locator("input.uk-checkbox");
        await expect(checkbox).toBeVisible();
        await expect(checkbox).not.toBeChecked();
      } else {
        // No checkbox: expect a tick mark button visible instead
        await expect(row.getByRole('button', { name: '✅', exact: true })).toBeVisible();
      }
    }
  });

  // Test 2: Tick one ungraduated page and verify it appears checked in Home watchlist
  test("tick an ungraduated page and verify in Home watchlist table", async ({ page }) => {
    const pages = await getUngraduatedWatchlistPages(page);
    const pageToTick = pages.find(p => p.hasCheckbox);
    if (!pageToTick) throw new Error("No ungraduated page with checkbox found");
    // Check checkbox is visible and unchecked
    const row = page.locator(`#${pageToTick.rowId}`);
    const checkbox = row.locator("input.uk-checkbox");
    await expect(checkbox).toBeVisible();
    await expect(checkbox).not.toBeChecked();

    // Tick the checkbox
    await tickWatchlistPage(page, pageToTick);
    // Verify in Home watchlist
    await verifyPageInHomeWatchlist(page, pageToTick);
  });
});
