import { test, expect } from '@playwright/test';

test('user_selection', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/user_selection');
  await expect(page.getByRole('link', { name: 'Select User' })).toBeVisible();
  await page.getByRole('link', { name: 'Home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/user_selection");
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page).toHaveURL("http://localhost:5001/user_selection");
  await page.getByRole('link', { name: 'Tables' }).click();
  await expect(page).toHaveURL("http://localhost:5001/user_selection");
  await expect(page.getByRole('button', { name: 'Switch User' }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Switch User' }).first().click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.getByRole('link', { name: 'Siraj' })).toBeVisible();
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page).toHaveURL("http://localhost:5001/revision");
  await page.getByRole('link', { name: 'Tables' }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables");
  await page.getByRole('link', { name: 'Siraj' }).click();
  await expect(page.getByRole('button', { name: 'Go to home' })).toBeVisible();
  await page.getByRole('button', { name: 'Go to home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
});


test('user_selection_with multi-user', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/user_selection');
  await page.getByRole('button', { name: 'Switch User' }).first().click();
  await expect(page.getByRole('link', { name: 'Siraj' })).toBeVisible();
  await page.getByRole('link', { name: 'Tables' }).click();
  await page.getByRole('link', { name: 'Users' }).click();
  await page.getByRole('button', { name: 'New' }).click();
  await page.getByRole('textbox', { name: 'name' }).click();
  await page.getByRole('textbox', { name: 'name' }).fill('Zaseem');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('cell', { name: 'Zaseem' }).first()).toBeVisible();
  await page.getByRole('link', { name: 'Siraj' }).click();
  await expect(page).toHaveURL("http://localhost:5001/user_selection");
  await expect(page.getByRole('heading', { name: 'Zaseem' }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: 'Switch User' }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Switch User' }).first().click();
  await expect(page.getByRole('link', { name: 'Zaseem' })).toBeVisible();
  await page.getByRole('link', { name: 'Zaseem' }).click();
  await expect(page).toHaveURL("http://localhost:5001/user_selection");
  await expect(page.getByRole('button', { name: 'Switch User' }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: 'Go to home' }).first()).toBeVisible();
});

