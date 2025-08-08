import { test, expect, Page } from "@playwright/test";

// Define interface for page data structure
interface PageData {
  status: string;
  testId: string;
  pageNumber: string;
}

test.describe("Full Cycle E2E Workflow", () => {
  // Test user credentials - unique per test run
  const testName = `testUser`;
  const testEmail = `test@example.com`;
  const testPassword = "Test123!@#";
  const testHafizName = "Test Hafiz";

  // Helper function to register a new user
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

  // Helper function to perform full login
  async function login(page: Page): Promise<void> {
    await page.goto("/users/login");
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password").fill(testPassword);
    await page.getByRole("button", { name: "Login" }).click();
  }

  // Helper function to create a new hafiz
  async function createAndSelectHafiz(page: Page, name: string): Promise<void> {
    await page.goto("/users/hafiz_selection");
    await page.getByRole("textbox", { name: "Name" }).fill(name);
    await page.getByRole("button", { name: "Add Hafiz" }).click();
    await page.getByTestId(`switch-${name}-hafiz-button`).click();
  }

  // Helper function to get hafiz ID by name
  async function getHafizId(page: Page, name: string): Promise<number> {
    await page.goto("/");
    await page.getByRole("link", { name: "Tables" }).click();
    await page.getByTestId("hafizs-link").click();

    // Find row with matching name and extract ID from first column
    const idText = await page
      .locator('[data-testid="hafizs-rows"] tr')
      .filter({ hasText: name })
      .locator('[data-testid="row-id"] a')
      .textContent();

    if (!idText) {
      throw new Error(`Hafiz with name "${name}" not found`);
    }

    return parseInt(idText.trim());
  }

  // Helper function to get hafiz ID by name
  async function getUserId(page: Page, name: string): Promise<number> {
    await page.goto("/");
    await page.getByRole("link", { name: "Tables" }).click();
    await page.getByTestId("users-link").click();

    // Find row with matching name and extract ID from first column
    const idText = await page
      .locator('[data-testid="users-rows"] tr')
      .filter({ hasText: name })
      .locator('[data-testid="row-id"] a')
      .textContent();

    if (!idText) {
      throw new Error(`User with name "${name}" not found`);
    }

    return parseInt(idText.trim());
  }

  let authStorageState: any;

  // Register and login user once before all tests, save auth state
  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();

    // Register new test user
    await registerUser(page);

    // Login with the new user
    await login(page);

    // Verify login was successful
    await expect(page).toHaveURL("/users/hafiz_selection");

    // Create a new hafiz
    await createAndSelectHafiz(page, testHafizName);

    // Verify hafiz creation was successful
    await expect(page).toHaveURL("/");

    // Save authentication state (cookies, localStorage, etc.)
    authStorageState = await page.context().storageState();

    await page.close();
  });

  test.beforeEach(async ({ page }) => {
    // Load the saved authentication state
    await page.context().addCookies(authStorageState.cookies || []);

    // Navigate to Home page
    await page.goto("/");
  });

  // Logout and delete test user after all tests
  test.afterAll(async ({ browser }) => {
    const context = await browser.newContext({
      storageState: authStorageState,
    });
    const page = await context.newPage();
    const userId = await getUserId(page, testName);

    // User cleanup
    // Delete the user account
    const deleteResponse = await page.request.delete(`/users/${userId}`);

    // Verify deletion was successful
    expect(deleteResponse.ok()).toBeTruthy();

    // Navigate to home page
    await page.goto("/");

    // Verify logout was successful
    await expect(page).toHaveURL("/users/login");

    // Login with deleted user
    await login(page);

    // Verify login was unsuccessful and redirects to signup page, as the user is deleted.
    await expect(page).toHaveURL("/users/signup");

    await page.close();
    await context.close();
  });

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

  // Helper function to create a new plan
  async function createNewPlan(page: Page, hafizName: string): Promise<void> {
    const hafizId: number = await getHafizId(page, hafizName);
    await page.getByRole("link", { name: "Tables" }).click();
    await page.getByTestId("plans-link").click();
    await page.getByRole("button", { name: "New" }).click();

    // Fill form with hafiz ID and start page
    await page.getByRole("spinbutton", { name: "hafiz_id" }).click();
    await page
      .getByRole("spinbutton", { name: "hafiz_id" })
      .fill(hafizId.toString());
    await page.getByRole("spinbutton", { name: "start_page" }).click();
    await page.getByRole("spinbutton", { name: "start_page" }).fill("2");
    await page.getByRole("radio", { name: "False" }).check();
    await page.getByRole("button", { name: "Save" }).click();
    await page.getByRole("link", { name: "Home" }).click();
    await expect(page).toHaveURL("/");
    await expect(
      page.getByTestId("monthly-cycle-summary-table-area")
    ).toBeVisible();
  }

  // Helper function to verify memorized pages are displayed correctly in home table
  async function verifyHomeTablePages(
    page: Page,
    expectedPages: PageData[]
  ): Promise<void> {
    await page.goto("/");
    await page.getByRole("button", { name: "+5" }).click();
    await page.waitForTimeout(1000);

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

    expect(titleElements.length).toEqual(expectedPageDetails.length);

    // Verify each expected page is displayed
    for (const titleElement of titleElements) {
      const parts = titleElement.split(" ");
      // Get the first part of the array
      const actualPage = parts[0];

      expect(expectedPageDetails).toContainEqual(actualPage);
    }
  }

  // verify gaps and input **after each selection**
  type Step = {
    selectPage: string;
    expectedPageGaps: string[];
    expectedInput: string | null;
  };

  async function verifyMonthlyCycleGapsAndInputs(page: Page, steps: Step[]) {
    const textbox = page.getByRole("textbox", {
      name: "Enter from page 2, format",
    });

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
      { status: "1", testId: "page-3-row", pageNumber: "3" },
      { status: "1", testId: "page-4-row", pageNumber: "4" },
      { status: "1", testId: "page-7-row", pageNumber: "7" },
      { status: "1", testId: "page-9-row", pageNumber: "9" },
      { status: "1", testId: "page-100-row", pageNumber: "100" },
    ];
    const monthlyCycleSteps: Step[] = [
      { selectPage: "3", expectedPageGaps: ["4"], expectedInput: "4" },
      { selectPage: "7", expectedPageGaps: ["4", "9"], expectedInput: "9" },
      { selectPage: "100", expectedPageGaps: ["4", "9"], expectedInput: "4" },
      { selectPage: "4", expectedPageGaps: ["9"], expectedInput: "9" },
      { selectPage: "9", expectedPageGaps: [], expectedInput: null },
    ];

    // Step 1: Set memorized pages in profile
    await setMemorizedPages(page, memorizedPages);

    // Step 2: Create new plan
    await createNewPlan(page, testHafizName);

    // Step 3: Verify home page displays only memorized pages correctly
    await verifyHomeTablePages(page, memorizedPages);

    // Step 4: Verify gaps and input after each revision selection
    await verifyMonthlyCycleGapsAndInputs(page, monthlyCycleSteps);
  });
});
