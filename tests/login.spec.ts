import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Login and select Siraj hafiz - common setup for all tests
  await page.goto('http://localhost:5001/login');
  await page.getByLabel('Email').fill('mailsiraj@gmail.com');
  await page.getByLabel('Password').fill('123');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).toHaveURL('http://localhost:5001/hafiz_selection');
  await page.getByRole('button', { name: 'Switch Hafiz' }).first().click();
  await expect(page).toHaveURL('http://localhost:5001/');
});

test('user can access main app after login and hafiz selection', async ({ page }) => {
  // Should be on main app page after beforeEach setup
  await expect(page).toHaveURL('http://localhost:5001/');
});