import { test, expect} from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:5001/login');
  await page.getByRole('textbox', { name: 'Email' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('mailsiraj@gmail.com');
  await page.getByRole('textbox', { name: 'Password' }).click();
  await page.getByRole('textbox', { name: 'Password' }).fill('123');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).toHaveURL("http://localhost:5001/hafiz_selection");
  await expect(page.getByRole('button', { name: 'Switch Hafiz' }).first()).toBeVisible();
  // await page.getByRole('button', { name: 'Switch Hafiz' }).first().click();
});

test('login_and_logout', async ({ page }) => {
  // Recording...
  await expect(page.getByRole('link', { name: 'logout' })).toBeVisible();
  await page.getByRole('link', { name: 'logout' }).click();
  await page.getByRole('textbox', { name: 'Email' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('mailsiraj@gmail.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('123');
  await page.getByRole('button', { name: 'Login' }).click();
  await page.getByRole('link', { name: 'logout' }).click();
  await page.getByRole('textbox', { name: 'Email' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('mailfiroz@gmail.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('123');
  await page.getByRole('button', { name: 'Login' }).click();
  await page.getByRole('link', { name: 'logout' }).click();
});

test('add_new_hafiz', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/hafiz_selection');
  await expect(page.getByRole('heading', { name: 'Add Hafiz' })).toBeVisible();
  await page.getByRole('textbox', { name: 'Hafiz Name' }).click();
  await page.getByRole('textbox', { name: 'Hafiz Name' }).fill('Adhil');
  await page.locator('uk-select').filter({ hasText: 'ChildTeenAdult Select an' }).getByRole('button').click();
  await page.locator('a').filter({ hasText: 'Adult' }).click();
  await page.getByRole('spinbutton', { name: 'Daily Capacity' }).click();
  await page.getByRole('spinbutton', { name: 'Daily Capacity' }).fill('5');
  await page.getByRole('button', { name: 'Select an option' }).click();
  await page.locator('a').filter({ hasText: 'Sibling' }).click();
  await page.getByRole('button', { name: 'Add Hafiz' }).click();
  await expect(page.getByRole('heading', { name: 'Adhil' }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Switch hafiz' }).first().click();
  await page.getByRole('link', { name: 'Tables' }).click({timeout: 2_000 });
  await page.getByRole('link', { name: 'Hafizs', exact: true }).click();
  page.on('dialog', dialog => dialog.accept());
  await page.locator('tr', { hasText: 'Adhil' }).getByRole('link', { name: 'Delete' }).first().click();
});

test('hafiz_selection', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/hafiz_selection');
  await expect(page.getByRole('link', { name: 'Select Hafiz' }).first()).toBeVisible();
  await page.getByRole('link', { name: 'Home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/hafiz_selection");
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page).toHaveURL("http://localhost:5001/hafiz_selection");
  await page.getByRole('link', { name: 'Tables' }).click();
  await expect(page).toHaveURL("http://localhost:5001/hafiz_selection");
  await expect(page.getByRole('button', { name: 'Switch Hafiz' }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Switch Hafiz' }).first().click();
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


test('multiple_users_can_access_same_hafiz', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/hafiz_selection');
  await expect(page.getByRole('heading', { name: 'Add Hafiz' })).toBeVisible();
  await page.getByRole('textbox', { name: 'Hafiz Name' }).click();
  await page.getByRole('textbox', { name: 'Hafiz Name' }).fill('Zaseem');
  await page.locator('uk-select').filter({ hasText: 'ChildTeenAdult Select an' }).getByRole('button').click();
  await page.locator('a').filter({ hasText: 'Adult' }).click();
  await page.getByRole('spinbutton', { name: 'Daily Capacity' }).click();
  await page.getByRole('spinbutton', { name: 'Daily Capacity' }).fill('4');
  await page.getByRole('button', { name: 'Select an option' }).click();
  await page.locator('a').filter({ hasText: 'Sibling' }).click();
  await page.getByRole('button', { name: 'Add Hafiz' }).click();
  await expect(page.getByRole('heading', { name: 'Zaseem' }).first()).toBeVisible();
  await page.locator('#btn-Zaseem').first().click();
  await expect(page.getByRole('link', { name: 'Zaseem' })).toBeVisible();
  await page.getByRole('link', { name: 'Zaseem' }).click();
  await expect(page).toHaveURL("http://localhost:5001/hafiz_selection");
  await expect(page.getByRole('button', { name: 'Switch Hafiz' }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: 'Go to home' })).toBeVisible();
  // TEST: multiple users can access same hafiz
  await page.goto('http://localhost:5001/hafiz_selection');
  await expect(page.getByRole('heading', { name: 'Zaseem' }).first()).toBeVisible();
  await page.locator('#btn-Zaseem').first().click();
  await expect(page.getByRole('link', { name: 'Zaseem' })).toBeVisible();
  // Create revisionship between Ibrahim (student) and Firoza(teacher)
  await page.getByRole('link', { name: 'Tables' }).click();
  await page.getByRole('link', { name: 'Hafizs_users' }).click();
  await page.getByRole('button', { name: 'New' }).click();
  await page.getByRole('spinbutton', { name: 'user_id', exact: true }).click();
  await page.getByRole('spinbutton', { name: 'user_id', exact: true }).fill('2');
  await page.getByRole('spinbutton', { name: 'hafiz_id' }).click();
  await page.getByRole('spinbutton', { name: 'hafiz_id' }).fill('3');
  await page.getByRole('button', { name: 'Select an option' }).first().click();
  await page.locator('a').filter({ hasText: 'Teacher' }).click();
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('heading', { name: 'Zaseem' })).toBeVisible();
  await page.getByRole('link', { name: 'Quran SRS' }).click();
  // add data as Zaseem from the user Siraj
  await expect(page.getByRole('link', { name: 'Zaseem' })).toBeVisible();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('200');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  // await expect(page).toHaveURL("http://localhost:5001/hafiz_selection");
  await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('1');
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('202');
  await page.getByRole('link', { name: 'logout' }).click();
  // login as Firoza
  await page.getByRole('textbox', { name: 'Email' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('mailfiroz@gmail.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('123');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page.getByRole('heading', { name: 'Zaseem' }).first()).toBeVisible();
  await page.locator('#btn-Zaseem').first().click();
  await expect(page.getByRole('link', { name: 'Zaseem' })).toBeVisible();
   await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('202');
  await page.getByRole('link', { name: '200 - 9. Tawbah -> 201 - 9. Tawbah' }).click();
  // modify data as Zaseem from the user Firoza

  await page.getByRole('row', { name: '9. Tawbah 200' }).first().getByLabel('❌ Bad').check();
  await page.getByRole('row', { name: '9. Tawbah 201' }).first().getByLabel('❌ Bad').check();
  await page.getByRole('button', { name: 'Save' }).click();
  page.on('dialog', dialog => dialog.accept());
  await page.locator('tr', { hasText: '201' }).first().getByRole('link', { name: 'Delete' }).click();
  await page.getByRole('link', { name: 'logout' }).click();
  // login as Siraj and ensure that the data is updated
  await page.getByRole('textbox', { name: 'Email' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('mailsiraj@gmail.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('123');
  await page.getByRole('button', { name: 'Login' }).click();
  await page.locator('#btn-Zaseem').first().click();
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('201');
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page.locator('tr', { hasText: '200'}).first()).toContainText('❌ Bad');
  await page.getByRole('link', { name: 'Zaseem' }).click();
  await page.getByRole('button', { name: 'Switch hafiz' }).first().click();
  await page.getByRole('link', { name: 'Tables' }).click();
  await page.getByRole('link', { name: 'Hafizs', exact: true }).click();
  // page.on('dialog', dialog => dialog.accept());
  await page.locator('tr', { hasText: 'Zaseem' }).getByRole('link', { name: 'Delete' }).click();
  await page.getByRole('link', { name: 'logout' }).click();
});