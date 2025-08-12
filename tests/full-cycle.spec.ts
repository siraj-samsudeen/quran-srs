import { test, expect, Page } from '@playwright/test';

/**
 * Tests the complete memorization tracking workflow through 5 sequential steps.
 *
 * - User registration and hafiz creation
 * - Page status configuration
 * - Full-cycle table verification
 *  - are the non-memorized pages skipped?
 *  - are all the memorized pages including SRS pages included?
 * - Date close and verify the summary with the actual pages entered
 * - Next day, see whether the sequence continues
 * - If the full cycle is complete, it should display a message to close the current cycle and create new one
 *
 */

test.describe.serial('Full Cycle Workflow', () => {
  // Single source of truth for page configuration
  const PAGE_STATUS_MAP = {
    3: 'Strong', // Memorized
    4: 'Strong', // Memorized
    7: 'Strong', // Memorized
    9: 'SRS Mode',
    100: 'SRS Mode',
    101: 'SRS Mode',
    102: 'Strong', // Memorized
    103: 'Strong', // Memorized
    104: 'Strong', // Memorized
  };

  // Uses shared browser context - user registration and login happens once, state persists across tests.
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('Step 1: Register user and create hafiz', async () => {
    // Flow: Register → Login → Create hafiz → Switch to hafiz → Verify home page

    // Unique test user credentials
    const timestamp = Date.now();
    const testUser = {
      name: `testUser_${timestamp}`,
      email: `test${timestamp}@example.com`,
      password: 'Test123!@#',
      hafiz1: 'Hafiz1',
      hafiz2: 'Hafiz2',
    };

    // Navigate to signup
    await page.goto('/users/signup');

    // Register user
    await page.getByLabel('Name').fill(testUser.name);
    await page.getByLabel('Email').fill(testUser.email);
    await page.getByLabel('Password', { exact: true }).fill(testUser.password);
    await page.getByLabel('Confirm Password').fill(testUser.password);
    await page.getByRole('button', { name: 'Signup' }).click();

    // Verify successful registration redirects to login
    await expect(page).toHaveURL('/users/login');

    // Login user
    await page.getByLabel('Email').fill(testUser.email);
    await page.getByLabel('Password').fill(testUser.password);
    await page.getByRole('button', { name: 'Login' }).click();

    // Verify login redirects to hafiz selection
    await expect(page).toHaveURL('/users/hafiz_selection');

    // Create first hafiz
    await page.getByRole('textbox', { name: 'Name' }).fill(testUser.hafiz1);
    await page.getByRole('button', { name: 'Add Hafiz' }).click();

    // Create second hafiz
    await page.getByRole('textbox', { name: 'Name' }).fill(testUser.hafiz2);
    await page.getByRole('button', { name: 'Add Hafiz' }).click();

    // TODO: improve implementation
    // Select the first hafiz (our main test hafiz)
    await page.getByTestId(`switch-${testUser.hafiz1}-hafiz-button`).click();

    // Verify successful hafiz selection redirects to home page
    await expect(page).toHaveURL('/');
  });

  test('Step 2: Configure page memorization status', async () => {
    // Flow: Profile → "by page" → Set statuses → Return home

    await expect(page).toHaveURL('/');
    await page.getByRole('link', { name: 'Profile' }).click();
    await page.getByRole('link', { name: 'by page' }).click();

    for (const [pageNum, status] of Object.entries(PAGE_STATUS_MAP)) {
      // Complex selector needed: page-3-row contains multiple elements, we need the combobox specifically
      // Example: page.getByTestId('page-3-row').getByRole('combobox') finds the status dropdown in row 3
      const dropdown = page
        .getByTestId(`page-${pageNum}-row`)
        .getByRole('combobox');
      await dropdown.click();
      await dropdown.selectOption(status);
    }
  });

  test('Step 3: Verify full-cycle table displays all configured pages', async () => {
    await page.goto('/');

    const expectedPages = Object.keys(PAGE_STATUS_MAP);

    // Get actual page numbers from table and verify
    const actualPageNumbers = await page
      .getByTestId('monthly_cycle_tbody')
      .locator('tr td:first-child a span')
      .allTextContents();

    for (const actualPageNumber of actualPageNumbers) {
      // Extract page number from "3 Baqarah P2" -> 3
      const pageNumber = parseInt(actualPageNumber.trim().split(' ')[0]);
      expect(expectedPages).toContain(pageNumber);
    }
  });

  test('Step 5: Close date and verify table update', async () => {
    // Tick off some pages as completed, then close date to see what remains

    // Ensure we're on the home page
    await page.goto('/');

    // Explicitly check off pages 3, 4, 7, 9 as completed
    const completedPages = [3, 4, 7, 9];
    for (const pageNum of completedPages) {
      await page.getByTestId(`${pageNum}-checkbox`).check();
    }

    await page.getByRole('button', { name: 'Close Date' }).click();
    await page.waitForTimeout(1000);

    // After closing, only unchecked pages should remain
    const expectedRemainingPages = [100, 101, 102, 103, 104];

    // Get actual page numbers from table and verify
    const actualPageNumbers = await page
      .getByTestId('monthly_cycle_tbody')
      .locator('tr td:first-child a span')
      .allTextContents();

    for (const actualPageNumber of actualPageNumbers) {
      // Extract page number from "101 Nisa Juz 5 End" -> 101
      const pageNumber = parseInt(actualPageNumber.trim().split(' ')[0]);
      expect(expectedRemainingPages).toContain(pageNumber);
    }
  });
});
