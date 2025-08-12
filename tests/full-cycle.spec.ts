import { test, expect, Page } from "@playwright/test";

// Define interface for page data structure
interface PageData {
  status: string;
  testId: string;
  pageNumber: string;
}
type Step = {
  selectPage: string;
  expectedPageGaps: string[];
  expectedInput: string | null;
};

test.describe("Full Cycle E2E Workflow", () => {
  // Test user credentials - unique per test run
  const testName = `testUser`;
  const testEmail = `test@example.com`;
  const testPassword = "Test123!@#";
  const testHafizName = "Test Hafiz";

  async function registerUser(page: Page): Promise<void> {
    await page.goto("/users/signup");

    // Fill registration form
    await page.getByLabel("Name").fill(testName);
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password", { exact: true }).fill(testPassword);
    await page.getByLabel("Confirm Password").fill(testPassword);

    // Submit registration
    await page.getByRole("button", { name: "Signup" }).click();

    // Verify registration success - should redirect to login or hafiz selection
    await expect(page).toHaveURL(/\/users\/login/);
  }

  async function login(page: Page): Promise<void> {
    await page.goto("/users/login");
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password").fill(testPassword);
    await page.getByRole("button", { name: "Login" }).click();
  }

  async function createHafiz(page: Page): Promise<void> {
    await page.goto("/users/hafiz_selection");
    await page.getByRole("textbox", { name: "Name" }).fill(testHafizName);
    await page.getByRole("button", { name: "Add Hafiz" }).click();
  }

  // Helper function to set specific pages with memorized status
  async function setMemorizedPages(
    page: Page,
    pages: PageData[]
  ): Promise<void> {
    await expect(page).toHaveURL("/");
    await page.getByRole("link", { name: "Profile" }).click();
    await page.getByRole("link", { name: "by page" }).click();

    // Set status for each page using dropdown
    for (const pageData of pages) {
      await page.getByTestId(pageData.testId).getByRole("combobox").click();
      await page
        .getByTestId(pageData.testId)
        .getByRole("combobox")
        .selectOption(pageData.status);
      await page.waitForTimeout(200);
    }
    await page.getByRole("link", { name: "Home" }).click();
    await expect(page).toHaveURL("/");
  }

  // Helper function to verify memorized pages are displayed correctly in home table
  async function verifyHomeTablePages(
    page: Page,
    expectedPages: PageData[]
  ): Promise<void> {
    await page.goto("/");

    // Extract expected page titles for comparison
    const expectedPageDetails: string[] = expectedPages.map(
      (pageData) => pageData.pageNumber
    );

    // Get actual page titles from the table
    let titleElements: string[] = await page
      .getByTestId("monthly_cycle_tbody")
      .locator("tr td:first-child a span")
      .allTextContents();

    titleElements = titleElements.map((title) => title.trim());

    // Verify each expected page is displayed
    for (const titleElement of titleElements) {
      const parts = titleElement.split(" ");
      // Get the first part of the array
      const actualPage = parts[0];

      expect(expectedPageDetails).toContainEqual(actualPage);
    }
  }

  async function verifyMonthlyCycleGapsAndInputs(page: Page, steps: Step[]) {
    const textbox = page.getByRole("textbox", {
      name: "Enter from page 2, format",
    });
    await page.getByRole("button", { name: "+5" }).click();
    await page.waitForTimeout(1000);

    for (const step of steps) {
      // Select the checkbox for the page
      // FIXME: This is not the best way to select the checkbox
      // We should find a better way to select the checkbox
      await page.getByTestId(`${step.selectPage}-checkbox`).check();

      await page.waitForTimeout(200);

      // If there are expected gaps, "Next" header should be visible and gaps should be visible
      if (step.expectedPageGaps.length > 0) {
        await expect(page.getByRole("cell", { name: "Next" })).toBeVisible();

        for (const gap of step.expectedPageGaps) {
          await expect(
            page
              .locator("#monthly_cycle_link_table")
              .locator("td", { hasText: gap })
          ).toBeVisible();
        }
      } else {
        // If no gaps expected, "Next" header should not be visible
        await expect(
          page.getByRole("cell", { name: "Next" })
        ).not.toBeVisible();
      }

      // Check input value
      if (step.expectedInput === null) {
        await expect(textbox).toBeEmpty();
      } else {
        await expect(textbox).toHaveValue(step.expectedInput);
      }
    }
  }

  // Main E2E test
  test("complete full-cycle workflow: create hafiz, set pages, create plan, verify home display, Verify gaps and input value", async ({
    page,
  }) => {
    // Test data
    const memorizedPages: PageData[] = [
      { status: "1", testId: "page-3-row", pageNumber: "3" }, // status: "1" means memorized
      { status: "1", testId: "page-4-row", pageNumber: "4" },
      { status: "1", testId: "page-7-row", pageNumber: "7" },
      { status: "5", testId: "page-9-row", pageNumber: "9" }, // status: "5" means SRS mode
      { status: "5", testId: "page-100-row", pageNumber: "100" },
      { status: "5", testId: "page-101-row", pageNumber: "101" },
      { status: "1", testId: "page-102-row", pageNumber: "102" },
      { status: "1", testId: "page-103-row", pageNumber: "103" },
      { status: "1", testId: "page-104-row", pageNumber: "104" },
    ];
    const monthlyCycleSteps: Step[] = [
      { selectPage: "3", expectedPageGaps: ["4"], expectedInput: "4" },
      { selectPage: "7", expectedPageGaps: ["4", "9"], expectedInput: "9" },
      {
        selectPage: "100",
        expectedPageGaps: ["4", "9", "101"],
        expectedInput: "101",
      },
      { selectPage: "4", expectedPageGaps: ["9", "101"], expectedInput: "9" },
      { selectPage: "9", expectedPageGaps: ["101"], expectedInput: "101" },
    ];

    await registerUser(page);

    await login(page);

    // Verify login was successful
    await expect(page).toHaveURL("/users/hafiz_selection");

    await createHafiz(page);

    // TODO
    // Select the created hafiz
    await page.getByTestId(`switch-${testHafizName}-hafiz-button`).click();

    // Verify hafiz creation was successful
    await expect(page).toHaveURL("/");

    await setMemorizedPages(page, memorizedPages);

    // Verify full-cycle were showing the first 5 pages
    await verifyHomeTablePages(page, memorizedPages.slice(0, 5));

    await verifyMonthlyCycleGapsAndInputs(page, monthlyCycleSteps);

    await page.getByRole("button", { name: "Close Date" }).click();

    // Wait for home table is updated
    await page.waitForTimeout(1000);

    // Verify full-cycle were showing rest of the pages after closing date
    await verifyHomeTablePages(page, memorizedPages.slice(5));
  });
});
