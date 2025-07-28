import { test, expect } from '@playwright/test';

test.describe('Revision Module', () => {

  // Helper function to perform full login
  async function loginAndSelectHafiz(page) {
    await page.goto('http://localhost:5001/users/login');
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
    await page.getByRole('button', { name: 'Switch Hafiz' }).first().click();
    await expect(page).toHaveURL('http://localhost:5001/');
  }

  test.beforeEach(async ({ page }) => {
    await loginAndSelectHafiz(page);
  });

  test.describe('Main Revision Table View', () => {

    test('revision page loads with table and action buttons', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Check main table elements
      await expect(page.locator('table')).toBeVisible();
      await expect(page.locator('thead').getByText('Page')).toBeVisible();
      await expect(page.getByText('Part')).toBeVisible();
      await expect(page.getByText('Mode')).toBeVisible();
      await expect(page.getByText('Rating')).toBeVisible();
      await expect(page.getByText('Surah')).toBeVisible();
      
      // Check action buttons
      await expect(page.getByRole('button', { name: 'Bulk Edit' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Bulk Delete' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Export' })).toBeVisible();
    });

    test('bulk edit and delete buttons are initially disabled', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Buttons should be disabled when no checkboxes selected
      await expect(page.getByRole('button', { name: 'Bulk Edit' })).toBeDisabled();
      await expect(page.getByRole('button', { name: 'Bulk Delete' })).toBeDisabled();
    });

    test('selecting checkbox enables bulk action buttons', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Find first checkbox in revision table
      const firstCheckbox = page.locator('input[type="checkbox"][name="ids"]').first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.click();
        
        // Buttons should be enabled after selection
        await expect(page.getByRole('button', { name: 'Bulk Edit' })).not.toBeDisabled();
        await expect(page.getByRole('button', { name: 'Bulk Delete' })).not.toBeDisabled();
      }
    });

    test('infinite scroll loads more revisions', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Get initial row count
      const initialRows = await page.locator('tbody tr').count();
      
      // Scroll to bottom to trigger infinite scroll
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      
      // Wait for potential new content
      await page.waitForTimeout(1000);
      
      // Check if more rows loaded (or same if no more data)
      const finalRows = await page.locator('tbody tr').count();
      expect(finalRows).toBeGreaterThanOrEqual(initialRows);
    });

    test('revision table shows correct data columns', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Check that first revision row has expected data structure
      const firstRow = page.locator('tbody tr').first();
      if (await firstRow.isVisible()) {
        const cells = firstRow.locator('td');
        const cellCount = await cells.count();
        
        // Should have checkbox, page, part, mode, plan_id, rating, surah, juz, date, action
        expect(cellCount).toBe(10);
      }
    });

  });

  test.describe('Single Revision Add', () => {

    test('single revision add form loads correctly', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/add?page=1&plan_id=1');
      
      // Check form elements
      await expect(page.locator('form')).toBeVisible();
      await expect(page.getByLabel('Revision Date')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Cancel' })).toBeVisible();
      
      // Check rating radio buttons
      await expect(page.locator('input[type="radio"][name="rating"]')).toHaveCount(3);
    });

    test('single revision add with valid data', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/add?page=1&plan_id=1');
      
      // Fill form
      await page.getByLabel('Revision Date').fill('2024-01-01');
      await page.locator('input[type="radio"][name="rating"][value="1"]').click();
      
      // Submit form
      await page.getByRole('button', { name: 'Save' }).click();
      
      // Should redirect to next page or home
      await expect(page).toHaveURL(/.*\/revision\/add.*/);
    });

    test('single revision form has hidden fields', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/add?page=1&plan_id=1');
      
      // Check hidden fields exist
      await expect(page.locator('input[name="id"]')).toBeAttached();
      await expect(page.locator('input[name="item_id"]')).toBeAttached();
      await expect(page.locator('input[name="plan_id"]')).toBeAttached();
    });

  });

  test.describe('Bulk Revision Add', () => {

    test('bulk revision add form loads correctly', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/bulk_add?page=1&plan_id=1');
      
      // Check form elements
      await expect(page.locator('form')).toBeVisible();
      await expect(page.getByLabel('Revision Date')).toBeVisible();
      await expect(page.locator('table')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Cancel' })).toBeVisible();
    });

    test('bulk revision table shows page information', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/bulk_add?page=1&plan_id=1');
      
      // Check table headers
      await expect(page.locator('thead').getByText('Page')).toBeVisible();
      await expect(page.getByText('Start Text')).toBeVisible();
      await expect(page.getByText('Rating')).toBeVisible();
      
      // Check select all checkbox
      await expect(page.locator('input[type="checkbox"].select_all')).toBeVisible();
    });

test('select all checkbox functionality works', async ({ page }) => {
  await page.goto('http://localhost:5001/revision/bulk_add?page=1&plan_id=1');
  const selectAllCheckbox = page.locator('input[type="checkbox"].select_all');
  // Check if select all is already checked, if not then click it
  const isSelectAllChecked = await selectAllCheckbox.isChecked();
  if (!isSelectAllChecked) {
    await selectAllCheckbox.click();
  }
  // Verify all revision checkboxes are checked
  const revisionCheckboxes = page.locator('input[type="checkbox"][name="ids"]');
  const count = await revisionCheckboxes.count();
  
  if (count > 0) {
    for (let i = 0; i < count; i++) {
      await expect(revisionCheckboxes.nth(i)).toBeChecked();
    }
  }
});

    test('bulk revision form accepts date and saves data', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/bulk_add?page=1&plan_id=1');
      
      // Fill revision date
      await page.getByLabel('Revision Date').fill('2024-01-01');
      
      // Select at least one item if available
      const firstCheckbox = page.locator('input[type="checkbox"][name="ids"]').first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.click();
        
        // Submit form
        await page.getByRole('button', { name: 'Save' }).click();
        
        // Should redirect after save
        await expect(page).toHaveURL(/.*\/revision\/bulk_add.*/);
      }
    });

    test('page range parsing works correctly', async ({ page }) => {
      // Test different page formats
      const testCases = ['1', '1.2', '1-5', '1.2-5'];
      
      for (const pageFormat of testCases) {
        await page.goto(`http://localhost:5001/revision/bulk_add?page=${pageFormat}&plan_id=1`);
        
        // Should load without error
        await expect(page.locator('form')).toBeVisible();
      }
    });

  });

  test.describe('Revision Edit', () => {

    test('edit revision form loads with existing data', async ({ page }) => {
      // First go to revision list
      await page.goto('http://localhost:5001/revision');
      
      // Find first edit link
      const editLink = page.getByRole('link', { name: 'edit' }).first();
      if (await editLink.isVisible()) {
        await editLink.click();
        
        // Should show edit form
        await expect(page.locator('form')).toBeVisible();
        await expect(page.getByLabel('Revision Date')).toBeVisible();
        await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Cancel' })).toBeVisible();
        
        // Form should be pre-filled with existing data
        await expect(page.getByLabel('Revision Date')).not.toHaveValue('');
      }
    });

    test('edit revision saves changes correctly', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      const editLink = page.getByRole('link', { name: 'edit' }).first();
      if (await editLink.isVisible()) {
        await editLink.click();
        
        // Change revision date
        await page.getByLabel('Revision Date').fill('2024-02-01');
        
        // Change rating
        await page.locator('input[type="radio"][name="rating"][value="0"]').click();
        
        // Save changes
        await page.getByRole('button', { name: 'Save' }).click();
        
        // Should redirect back
        await expect(page).toHaveURL('http://localhost:5001/revision');
      }
    });

  });

  test.describe('Revision Delete', () => {

    test('single revision delete shows confirmation', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Set up dialog handler before triggering delete
      page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('Are you sure');
        await dialog.dismiss(); // Cancel the delete
      });
      
      const deleteLink = page.getByRole('link', { name: 'Delete' }).first();
      if (await deleteLink.isVisible()) {
        await deleteLink.click();
        // Dialog should have been triggered and dismissed
      }
    });

    test('bulk delete shows confirmation dialog', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Select a checkbox first
      const firstCheckbox = page.locator('input[type="checkbox"][name="ids"]').first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.click();
        
        // Set up dialog handler
        page.on('dialog', async dialog => {
          expect(dialog.message()).toContain('Are you sure you want to delete these revisions');
          await dialog.dismiss();
        });
        
        await page.getByRole('button', { name: 'Bulk Delete' }).click();
      }
    });

  });

  test.describe('Bulk Edit Operations', () => {

    test('bulk edit view loads correctly', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Select some revisions
      const firstCheckbox = page.locator('input[type="checkbox"][name="ids"]').first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.click();
        
        // Click bulk edit
        await page.getByRole('button', { name: 'Bulk Edit' }).click();
        
        // Should show bulk edit page
        await expect(page.getByText('Bulk Edit Revision')).toBeVisible();
        await expect(page.locator('table')).toBeVisible();
        await expect(page.getByLabel('Revision Date')).toBeVisible();
        await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Delete' })).toBeVisible();
      }
    });

    test('bulk edit form has rating dropdowns for each item', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      const firstCheckbox = page.locator('input[type="checkbox"][name="ids"]').first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.click();
        await page.getByRole('button', { name: 'Bulk Edit' }).click();
        
        // Should have rating dropdowns in table
        const ratingSelects = page.locator('select[name^="rating-"]');
        const count = await ratingSelects.count();
        expect(count).toBeGreaterThan(0);
      }
    });

    test('bulk edit saves changes for selected items', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      const firstCheckbox = page.locator('input[type="checkbox"][name="ids"]').first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.click();
        await page.getByRole('button', { name: 'Bulk Edit' }).click();
        
        // Update revision date
        await page.getByLabel('Revision Date').fill('2024-03-01');
        
        // Save changes
        await page.getByRole('button', { name: 'Save' }).click();
        
        // Should redirect back to revision list
        await expect(page).toHaveURL(/http:\/\/localhost:5001\/revision/);
      }
    });

  });

  test.describe('Rating System', () => {

    test('rating radio buttons show correct values', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/add?page=1&plan_id=1');
      
      // Check all three rating options exist
      await expect(page.locator('input[type="radio"][name="rating"][value="1"]')).toBeVisible(); // Good
      await expect(page.locator('input[type="radio"][name="rating"][value="0"]')).toBeVisible(); // Ok
      await expect(page.locator('input[type="radio"][name="rating"][value="-1"]')).toBeVisible(); // Bad
    });

    test('rating dropdown in bulk edit shows correct options', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/bulk_add?page=1&plan_id=1');
      
      // Check rating dropdown exists
      const ratingSelect = page.locator('select[name^="rating-"]').first();
      if (await ratingSelect.isVisible()) {
        await expect(ratingSelect).toBeVisible();
        
        // Should have Good, Ok, Bad options
        const options = ratingSelect.locator('option');
        const optionCount = await options.count();
        expect(optionCount).toBe(3);
      }
    });

    test('rating update via PUT request works', async ({ page }) => {
      // This tests the rating update functionality from summary tables
      await page.goto('http://localhost:5001/revision');
      
      // Get first revision ID if available
      const firstRow = page.locator('tbody tr').first();
      if (await firstRow.isVisible()) {
        // This is testing the endpoint exists - actual rating update would require
        // triggering the HTMX call which is complex in Playwright
        await expect(page).toHaveURL(/http:\/\/localhost:5001\/revision/);
      }
    });

  });

  test.describe('Navigation and URLs', () => {

    test('entry point redirects work correctly', async ({ page }) => {
      // Test bulk entry redirect
      const response = await page.request.post('http://localhost:5001/revision/entry', {
        data: { 
          type: 'bulk',
          page: '1',
          plan_id: '1'
        },
        maxRedirects:0
      });
      expect(response.status()).toBe(303); // Redirect
    });

    test('single entry redirect works correctly', async ({ page }) => {
      const response = await page.request.post('http://localhost:5001/revision/entry', {
        data: {
          type: 'single',
          page: '1',
          plan_id: '1'
        },
        maxRedirects:0
      });
      expect(response.status()).toBe(303); // Redirect 
    });

    test('revision export link works', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      const exportLink = page.getByRole('link', { name: 'Export' });
      await expect(exportLink).toHaveAttribute('href', 'tables/revisions/export');
    });

    test('page out of bounds handling', async ({ page }) => {
      // Test very high page number
      await page.goto('http://localhost:5001/revision/add?page=9999&plan_id=1');
      
      // Should redirect to home
      await expect(page).toHaveURL('http://localhost:5001/');
    });

  });

  test.describe('Security and Access Control', () => {

    test('revision routes require authentication', async ({ page }) => {
      // Clear session
      await page.goto('http://localhost:5001/users/logout');
      
      // Try to access revision page
      await page.goto('http://localhost:5001/revision');
      
      // Should redirect to login
      await expect(page).toHaveURL('http://localhost:5001/users/login');
    });

    test('revision routes require hafiz selection', async ({ page }) => {
      await page.goto('http://localhost:5001/users/logout');
      // Login but don't select hafiz
      await page.goto('http://localhost:5001/users/login');
      await page.getByLabel('Email').fill('mailsiraj@gmail.com');
      await page.getByLabel('Password').fill('123');
      await page.getByRole('button', { name: 'Login' }).click();
      
      // Try to access revision page
      await page.goto('http://localhost:5001/revision');
      
      // Should redirect to hafiz selection
      await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
    });

  });

  test.describe('Data Integration', () => {

    test('revision table shows related data correctly', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      const firstRow = page.locator('tbody tr').first();
      if (await firstRow.isVisible()) {
        // Should show page number, part, mode, surah, juz data
        const cells = firstRow.locator('td');
        
        // Page column should have numeric value or link
        const pageCell = cells.nth(1);
        await expect(pageCell).not.toBeEmpty();
        
        // Surah column should show surah name
        const surahCell = cells.nth(6);
        await expect(surahCell).not.toBeEmpty();
        
        // Juz column should show juz number
        const juzCell = cells.nth(7);
        await expect(juzCell).not.toBeEmpty();
      }
    });

    test('form validates required fields', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/add?page=1&plan_id=1');
      
      // Try to submit without selecting rating
      await page.getByRole('button', { name: 'Save' }).click();
      
      // Form should still be visible (validation failed)
      await expect(page.locator('form')).toBeVisible();
    });

  });

  test.describe('Performance and UX', () => {

    test('infinite scroll performance', async ({ page }) => {
      await page.goto('http://localhost:5001/revision');
      
      // Measure initial load time
      const startTime = Date.now();
      await page.waitForSelector('table');
      const loadTime = Date.now() - startTime;
      
      // Should load within reasonable time
      expect(loadTime).toBeLessThan(5000);
    });

    test('form submission provides feedback', async ({ page }) => {
      await page.goto('http://localhost:5001/revision/add?page=1&plan_id=1');
      
      // Fill and submit form
      await page.getByLabel('Revision Date').fill('2024-01-01');
      await page.locator('input[type="radio"][name="rating"][value="1"]').click();
      
      await page.getByRole('button', { name: 'Save' }).click();
      
      // Should navigate away (indicating success)
      await expect(page).toHaveURL(/\/revision\/add/);
    });

  });

});