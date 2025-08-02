import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {

  test('successful login redirects to hafiz selection', async ({ page }) => {
    await page.goto('http://localhost:5001/users/login');
    
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    
    await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
  });

  test('login with wrong email shows login page', async ({ page }) => {
    await page.goto('http://localhost:5001/users/login');
    
    await page.getByLabel('Email').fill('wrong@email.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    
    await expect(page).toHaveURL('http://localhost:5001/users/login');
  });

  test('login with wrong password shows login page', async ({ page }) => {
    await page.goto('http://localhost:5001/users/login');
    
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Login' }).click();
    
    await expect(page).toHaveURL('http://localhost:5001/users/login');
  });

  test('login with empty email shows login page', async ({ page }) => {
    await page.goto('http://localhost:5001/users/login');
    
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    
    await expect(page).toHaveURL('http://localhost:5001/users/login');
  });

  test('login with empty password shows login page', async ({ page }) => {
    await page.goto('http://localhost:5001/users/login');
    
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByRole('button', { name: 'Login' }).click();
    
    await expect(page).toHaveURL('http://localhost:5001/users/login');
  });

  test('logout clears session and redirects to login', async ({ page }) => {
    // First login
    await page.goto('http://localhost:5001/users/login');
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
    
    // Then logout
    await page.goto('http://localhost:5001/users/logout');
    await expect(page).toHaveURL('http://localhost:5001/users/login');
    
    // Verify session is cleared by trying to access protected page
    await page.goto('http://localhost:5001/');
    await expect(page).toHaveURL('http://localhost:5001/users/login');
  });

});

test.describe('Hafiz Selection', () => {

  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:5001/users/login');
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
  });

  test('hafiz selection page shows available hafiz accounts', async ({ page }) => {
    await expect(page.getByText('Hafiz Selection')).toBeVisible();
    await expect(page.getByText('Siraj')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Switch Hafiz' }).first()).toBeVisible();
  });

  test('switching hafiz redirects to main application', async ({ page }) => {
    await page.getByRole('button', { name: 'Switch Hafiz' }).first().click();
    await expect(page).toHaveURL('http://localhost:5001/');
  });

  test('add hafiz form is visible', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Add Hafiz' })).toBeVisible();
    await expect(page.getByLabel('Name')).toBeVisible();
    await expect(page.locator('uk-select[name="age_group"] >> button.uk-input-fake')).toBeVisible();
    await expect(page.getByLabel('Daily Capacity')).toBeVisible(); 
    await expect(page.locator('uk-select[name="relationship"] >> button.uk-input-fake')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add Hafiz' })).toBeVisible();
  });

  test('adding new hafiz with valid data', async ({ page }) => {
    await page.getByLabel('Name').fill('Test Hafiz');
    await page.locator('uk-select[name="age_group"] >> button.uk-input-fake').click()
    await page.locator('uk-select[name="age_group"]  >> a').filter({ hasText: 'Adult' }).click();
    await page.getByLabel('Daily Capacity').fill('5');
    await page.locator('uk-select[name="relationship"] >> button.uk-input-fake').click()
    await page.locator('uk-select[name="relationship"]  >> a').filter({ hasText: 'Sibling' }).click();
    await page.getByRole('button', { name: 'Add Hafiz' }).click();
    
    await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
    await expect(page.getByText('Test Hafiz').first()).toBeVisible();
  });

});

test.describe('Session Management', () => {

  test('accessing protected route without login redirects to login', async ({ page }) => {
    await page.goto('http://localhost:5001/');
    await expect(page).toHaveURL('http://localhost:5001/users/login');
  });

  test('accessing protected route without hafiz selection redirects to hafiz selection', async ({ page }) => {
    // Login but don't select hafiz
    await page.goto('http://localhost:5001/users/login');
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
    
    // Try to access main app directly - should stay on hafiz selection
    await page.goto('http://localhost:5001/');
    await expect(page).toHaveURL('http://localhost:5001/users/hafiz_selection');
  });

  test('session persists across page navigation after full login', async ({ page }) => {
    // Complete login flow
    await page.goto('http://localhost:5001/users/login');
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.getByRole('button', { name: 'Switch Hafiz' }).first().click();
    await expect(page).toHaveURL('http://localhost:5001/');
    
    // Navigate to different pages and verify session is maintained
    await page.goto('http://localhost:5001/profile/surah');
    await expect(page).not.toHaveURL('http://localhost:5001/users/login');
    
    await page.goto('http://localhost:5001/revision');
    await expect(page).not.toHaveURL('http://localhost:5001/users/login');
  });

});

test.describe('UI Components', () => {

  test('login form has proper labels and inputs', async ({ page }) => {
    await page.goto('http://localhost:5001/users/login');
    
    await expect(page.getByLabel('Email')).toHaveAttribute('type', 'email');
    await expect(page.getByLabel('Password')).toHaveAttribute('type', 'password');
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
  });

  test('login form has correct action attribute', async ({ page }) => {
    await page.goto('http://localhost:5001/users/login');
    
    const form = page.locator('form');
    await expect(form).toHaveAttribute('action', '/users/login');
    await expect(form).toHaveAttribute('method', 'post');
  });

  test('hafiz card shows proper button text based on selection state', async ({ page }) => {
    // Login and go to hafiz selection
    await page.goto('http://localhost:5001/users/login');
    await page.getByLabel('Email').fill('mailsiraj@gmail.com');
    await page.getByLabel('Password').fill('123');
    await page.getByRole('button', { name: 'Login' }).click();
    
    // Should show "Switch Hafiz" when not selected
    await expect(page.getByRole('button', { name: 'Switch Hafiz' }).first()).toBeVisible();
  });

});