import { test, expect } from '@playwright/test';

test('list_of_tables', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/tables');
  await page.getByRole('link', { name: 'Tables' }).click();
  // check if the list of tables are visible
  await expect(page.getByRole('link', { name: 'modes' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'pages' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'plans' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'revisions' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'users' })).toBeVisible();
});

test('modes_table', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/tables');
  await page.getByRole('link', { name: 'Tables' }).click();
  await expect(page.getByRole('link', { name: 'modes' })).toBeVisible();
  await page.getByRole('link', { name: 'modes' }).click();
  // check if the table is visible
  await expect(page.locator('#row-1')).toContainText('SEQ');
  await expect(page.locator('#row-2')).toContainText('SRS');
  await expect(page.locator('#row-3')).toContainText('Watch List');
  await expect(page.locator('#row-4')).toContainText('New Memorization');
  // update mode description
  await page.getByRole('link', { name: '1' }).click();
  await expect(page.getByRole('textbox', { name: 'name' })).toHaveValue('SEQ');
  await page.getByRole('textbox', { name: 'description' }).click();
  await page.getByRole('textbox', { name: 'description' }).fill('Added test description for update SEQ');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page).toHaveURL('http://localhost:5001/tables/modes');
  await expect(page.locator('#row-1')).toContainText('Added test description for update SEQ');
  // Add new mode
  await page.getByRole('button', { name: 'New' }).click();
  await page.getByRole('textbox', { name: 'name' }).click();
  await page.getByRole('textbox', { name: 'name' }).fill('Test - New Mode');
  await page.getByRole('button', { name: 'Save' }).click();
  // delete mode
  page.on('dialog', dialog => dialog.accept());
  await page.locator('#row-5').getByRole('link', { name: 'Delete' }).click();
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables");
  await expect(page.getByRole('link', { name: 'modes' })).toBeVisible();
});

test('pages_table', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/tables');
  await page.getByRole('link', { name: 'Tables' }).click();
  await expect(page.getByRole('link', { name: 'pages' })).toBeVisible();
  await page.getByRole('link', { name: 'pages' }).click();
  await expect(page.locator('#row-604')).toContainText('604'); //last page of quran
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables");
  await expect(page.getByRole('link', { name: 'pages' })).toBeVisible();
});

test('plan_and_revision_tables', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/tables');
  await page.getByRole('link', { name: 'Tables' }).click();
  // plans
  await expect(page.getByRole('link', { name: 'plans' })).toBeVisible();
  // revisions
  await expect(page.getByRole('link', { name: 'revisions' })).toBeVisible();
});

test('user_table_CRUD', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/tables');
  await page.getByRole('link', { name: 'Tables' }).click();
  await expect(page.getByRole('link', { name: 'users' })).toBeVisible();
  await page.getByRole('link', { name: 'users' }).click();
  // add new user
  await page.getByRole('button', { name: 'New' }).click();
  await page.getByRole('textbox', { name: 'name' }).click();
  await page.getByRole('textbox', { name: 'name' }).fill('Adhil');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables/users");
  await expect(page.getByRole('cell', { name: 'Adhil' })).toBeVisible();
  // update user details
  const row = page.locator('tr', { has: page.getByRole('cell', { name: 'Adhil' }) });
  await row.locator('a').first().click();
  await page.getByRole('textbox', { name: 'name' }).click();
  await page.getByRole('textbox', { name: 'name' }).fill('Adhil Madhani');
  await page.getByRole('textbox', { name: 'email' }).click();
  await page.getByRole('textbox', { name: 'email' }).fill('adhil@bisquared.com');
  await page.getByRole('textbox', { name: 'password' }).click();
  await page.getByRole('textbox', { name: 'password' }).fill('Abcd1234');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables/users");
  await expect(page.getByRole('cell', { name: 'Adhil Madhani' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'adhil@bisquared.com' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Abcd1234' })).toBeVisible();
  // delete specific user
  page.on('dialog', dialog => dialog.accept());
  await row.getByRole('link', { name: 'Delete' }).click();
  // back to tables
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables");
});


test('visibility_export_import_for_tables', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/tables');
  await page.getByRole('link', { name: 'modes' }).click();
  await expect(page.getByRole('button', { name: 'Export' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Import' })).toBeVisible();
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await page.getByRole('link', { name: 'pages' }).click();
  await expect(page.getByRole('button', { name: 'Export' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Import' })).toBeVisible();
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await page.getByRole('link', { name: 'plans' }).click();
  await expect(page.getByRole('button', { name: 'Export' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Import' })).toBeVisible();
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await page.getByRole('link', { name: 'revisions' }).click();
  await expect(page.getByRole('button', { name: 'Export' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Import' })).toBeVisible();
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await page.getByRole('link', { name: 'users' }).click();
  await expect(page.getByRole('button', { name: 'Export' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Import' })).toBeVisible();
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
});

test('modes_export_import', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/tables');
  await page.getByRole('link', { name: 'modes' }).click();
  await expect(page.getByRole('button', { name: 'Export' })).toBeVisible();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export' }).click();
  const download = await downloadPromise;
  // ensure that the downloaded file is a CSV
  const path = await download.path();
  console.log('Downloaded file path:', path);
  expect(download.suggestedFilename()).toMatch(/\.csv$/);
  await page.getByRole('link', { name: '1' }).click();
  await page.getByRole('textbox', { name: 'description' }).click();
  await page.getByRole('textbox', { name: 'description' }).fill('Not Imported yet');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('button', { name: 'Import' })).toBeVisible();
  await page.getByRole('button', { name: 'Import' }).click();
  await page.getByRole('button', { name: 'Choose File' }).click();
  await page.getByRole('button', { name: 'Choose File' }).setInputFiles('tests\\mode_import_for_test.csv');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#row-1')).toContainText('Imported file - Done');
  await page.getByRole('link').filter({ hasText: /^$/ }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables");
});