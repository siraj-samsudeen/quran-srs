import { test, expect } from '@playwright/test';

// Need to import master data before running the test.
// #TODO: During run all test, few test fails sometimes, need to figure out why.

// dymamically get the current date
const now = new Date();
const currentDate = now.toISOString().split('T')[0];

// before each test, go to the user selection page and switch to the first user
test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:5001/login');
  await page.getByRole('textbox', { name: 'Email' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('mailsiraj@gmail.com');
  await page.getByRole('textbox', { name: 'Password' }).click();
  await page.getByRole('textbox', { name: 'Password' }).fill('123');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).toHaveURL("http://localhost:5001/hafiz_selection");
  await expect(page.getByRole('button', { name: 'Switch Hafiz' }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Switch Hafiz' }).first().click();
});

test('navigation', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('link', { name: 'Quran SRS' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page).toHaveURL("http://localhost:5001/revision ");
  await page.getByRole('link', { name: 'Tables' }).click();
  await expect(page).toHaveURL("http://localhost:5001/tables");
  await page.getByRole('link', { name: 'Home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
});

test('single_entry', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('2');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate); 
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('2');
  await expect(page.getByText('Rating ✅ Good 😄 Ok ❌ Bad')).toBeVisible();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).fill('1');
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.getByRole('listitem').filter({ hasText: 'SRS' }).locator('a').click();
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.locator('h1')).toContainText('3 - 2 Al-Baqarah - إِنَّ الَّذِينَ كَفَرُوا');
  await expect(page.getByRole('button', { name: 'SRS' })).toBeVisible();
  await page.locator('body').press('Tab');
  await expect(page.getByRole('spinbutton', { name: 'Plan ID' })).toHaveValue('1');
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate); 
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('3');
  await expect(page.getByText('Rating ✅ Good 😄 Ok ❌ Bad')).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.locator('#main')).toContainText('2 - 2 Al-Baqarah');
});

test('bulk_entry', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('3');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.locator('h1')).toContainText('3 - 2 Al-Baqarah  => 7 - 2 Al-Baqarah');
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate); 
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.locator('a').filter({ hasText: 'New Memorization' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).fill('1');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('heading', { name: '8 - 2 Al-Baqarah => 12 - 2' })).toBeVisible();
  await expect(page.locator('uk-select')).toContainText('New Memorization');
  await expect(page.getByRole('button', { name: 'New Memorization' })).toBeVisible();
  await expect(page.getByRole('spinbutton', { name: 'Plan ID' })).toHaveValue('1');
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate);
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
});


test('revision_single_update', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('22');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate); //TODO Add current date
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('22');
  await expect(page.getByText('Rating ✅ Good 😄 Ok ❌ Bad')).toBeVisible();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).fill('1');
  await page.getByRole('button', { name: 'Save' }).click();
  // revision single update
  await page.getByRole('link', { name: 'Revision'}).click();
  await expect(page.getByRole('button',{name:'Export'})).toBeVisible();
  await page.getByRole('link', { name: '22' }).click();
  await expect(page.locator('h1')).toContainText('Edit Revision');
  await page.getByRole('textbox', { name: 'Revision Date' }).fill('2025-04-21');
  await page.getByRole('radio', { name: '😄 Ok' }).check();
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page).toHaveURL("http://localhost:5001/revision");
  await page.getByRole('link', { name: '22' }).click();
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('22');
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue('2025-04-21');
  await expect(page.getByRole('radio', { name: '😄 Ok' })).toBeChecked();
  await page.getByRole('link', { name: 'Home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
});


test('revision_bulk_update', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('99.2');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).fill('1');
  await expect(page.locator('h1')).toContainText('99 - 4 An-Nisa => 100 - 4 An-Nisa');
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate); //TODO Add current date
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.getByRole('listitem').filter({ hasText: 'SEQ' }).locator('a').click();
  await page.getByRole('button', { name: 'Save' }).click();
  // bulk update revision data
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page).toHaveURL("http://localhost:5001/revision");
  await expect(page.getByRole('button',{name:'Export'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Bulk Edit'})).toBeDisabled();
  await expect(page.getByRole('button',{name:'Bulk Delete'})).toBeDisabled();
  await page.getByRole('row', { name: '99 1 1 ✅ Good 4 An-Nisa 5' }).getByRole('checkbox').check();
  await page.getByRole('row', { name: '100 1 1 ✅ Good 4 An-Nisa 5' }).getByRole('checkbox').check();
  await expect(page.getByRole('button',{name:'Bulk Edit'})).toBeEnabled();
  await expect(page.getByRole('button',{name:'Bulk Delete'})).toBeEnabled();
  await page.getByRole('button', { name: 'Bulk Edit' }).click();
  await page.getByRole('row', { name: 'page 100 An-Nisa' }).getByLabel('❌ Bad').check();
  await page.getByRole('row', { name: 'page 99 An-Nisa' }).getByLabel('❌ Bad').check();
  await page.getByRole('textbox', { name: 'Revision Date' }).fill('2025-04-20');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page).toHaveURL("http://localhost:5001/revision");
  await expect(page.getByRole('row', { name: '100 1 1 ❌ Bad 4 An-Nisa 5' }).getByRole('checkbox')).toBeVisible();
  await expect(page.getByRole('row', { name: '99 1 1 ❌ Bad 4 An-Nisa 5' }).getByRole('checkbox')).toBeVisible();
  await page.getByRole('link', { name: 'Home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
});


test('export_revisions', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page).toHaveURL("http://localhost:5001/revision");
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export' }).click();
  const download = await downloadPromise;
  // ensure that the downloaded file is a CSV
  const path = await download.path();
  console.log('Downloaded file path:', path);
  expect(download.suggestedFilename()).toMatch(/\.csv$/); 
});


test('bulk_edit_revision_range', async ({ page }) => {
  // Recording...
 await page.goto('http://localhost:5001/');
 await page.getByRole('textbox', { name: 'page' }).click();
 await page.getByRole('textbox', { name: 'page' }).fill('33');
 await page.getByRole('button', { name: 'Bulk Entry' }).click();
 await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
 await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('1');
 await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
 await page.getByRole('listitem').filter({ hasText: 'SEQ' }).locator('a').click();
 await page.getByRole('button', { name: 'Save' }).click();
 await expect(page.getByRole('heading', { name: '38 - 2 Al-Baqarah => 42 - 2 Al-Baqarah' })).toBeVisible();
 await page.getByRole('button', { name: 'Cancel' }).click();
 await expect(page).toHaveURL("http://localhost:5001/");
//  bulk edit from revision range
 await page.getByRole('link', { name: '- 2 Al-Baqarah -> 37 - 2 Al-Baqarah' }).click();
 await page.getByRole('button', { name: 'Cancel' }).click();
 await expect(page).toHaveURL("http://localhost:5001/");
 await page.getByRole('link', { name: '- 2 Al-Baqarah -> 37 - 2 Al-Baqarah' }).click();
 await page.getByRole('row', { name: 'page 33 Al-Baqarah' }).getByLabel('😄 Ok').check();
 await page.getByRole('row', { name: 'page 34 Al-Baqarah' }).getByLabel('😄 Ok').check();
 await page.getByRole('row', { name: 'page 35 Al-Baqarah' }).getByLabel('😄 Ok').check();
 await page.getByRole('button', { name: 'Save' }).click();
 expect(page.url()).toContain("http://localhost:5001/revision");
 await expect(page.getByRole('row', { name: '37 1 1 ✅ Good 2 Al-Baqarah 2' })).toBeVisible();
 await expect(page.getByRole('row', { name: '36 1 1 ✅ Good 2 Al-Baqarah 2' })).toBeVisible();
 await expect(page.getByRole('row', { name: '35 1 1 😄 Ok 2 Al-Baqarah 2' })).toBeVisible();
 await expect(page.getByRole('row', { name: '34 1 1 😄 Ok 2 Al-Baqarah 2' })).toBeVisible();
 await expect(page.getByRole('row', { name: '33 1 1 😄 Ok 2 Al-Baqarah 2' })).toBeVisible();

});



test('continue_with_bulk_add', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('55');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.locator('uk-select[name="mode_id"]  >> a').filter({ hasText: 'Sequential' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).fill('2');
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await page.getByRole('link', { name: 'Quran SRS' }).click();
  //enable continue with bulk add
  await expect(page.getByText("56 - 3 Ali 'Imran")).toBeVisible();
  await page.getByRole('link', { name: "56 - 3 Ali 'Imran" }).click();
  await expect(page.getByText('Mode Id SequentialSRSNew')).not.toBeVisible();
  await expect(page.locator('div').filter({ hasText: 'Plan ID' }).nth(2)).not.toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();
  expect(page.url()).toContain("mode_id=1");
  expect(page.url()).toContain("plan_id=2"); 
  await expect(page.getByText('Mode Id SequentialSRSNew')).not.toBeVisible();
  await expect(page.locator('div').filter({ hasText: 'Plan ID' }).nth(2)).not.toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('link', { name: '61 - 3 Ali \'Imran' })).toBeVisible();
  await expect(page).toHaveURL("http://localhost:5001/");
});

test('bulk_delete', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('66');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('1');
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.getByRole('listitem').filter({ hasText: 'SEQ' }).locator('a').click();
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  // bulk delete
  await page.getByRole('link', { name: 'Revision' }).click();
  await page.getByRole('row', { name: "66 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox').first().check();
  await page.getByRole('row', { name: "67 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox').first().check();
  await page.getByRole('row', { name: "68 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox').first().check();
  await page.getByRole('row', { name: "69 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox').first().check();
  await page.getByRole('row', { name: "70 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox').first().check();
  page.on('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Bulk Delete' }).click();
  await expect(page.getByRole('row', { name: "66 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: "67 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: "68 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: "69 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: "70 1 1 ✅ Good 3 Ali 'Imran" }).getByRole('checkbox')).not.toBeVisible();
  await page.getByRole('link', { name: 'Home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
});



test('single_delete', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('77');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('1');
  await page.getByRole('button', { name: 'Save' }).click();
  // single delete
  await page.getByRole('link', { name: 'Revision' }).click();
  page.on('dialog', dialog => dialog.accept());
  await page.locator('tr', { hasText: '77' }).getByRole('link', { name: 'Delete' }).click();
  await expect(page.getByRole('row', { name: '77 1 1 ✅ Good 4. An Nisa Juz' }).getByRole('checkbox')).not.toBeVisible();
  await page.getByRole('link', { name: 'Home' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
});


test('bulk_add_with_custom_range', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('155.10');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('1');
  await expect(page.getByRole('heading', { name: '155 - 7 Al-A\'raf => 164 - 7 Al-A\'raf' })).toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();
  expect(page.url()).toContain("http://localhost:5001/revision/bulk_add?page=");
  await expect(page.getByRole('heading', { name: '165 - 7 Al-A\'raf => 174 - 7' })).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.getByText('155 - 7 Al-A\'raf').first()).toBeVisible();
});


test('single_add_with_custom_range', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('255.10');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('2');
  await expect(page.getByRole('heading', { name: '255 - 13 Ar-Ra\'d' })).toBeVisible();
  await page.getByRole('row', { name: 'page 255 Ar-Ra\'d' }).getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Save' }).click();
  expect(page.url()).toContain("http://localhost:5001/revision/add?page=");
  await expect(page.getByRole('heading', { name: '256 - 14 Ibrahim' })).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.getByText('255 - 13 Ar-Ra\'d').first()).toBeVisible();
});


test('shift_selection', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('355');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('2');
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.getByRole('listitem').filter({ hasText: 'SEQ' }).locator('a').click();
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('link', { name: '- 24 An-Nur -> 359 - 24 An-Nur' }).click();
  await page.getByRole('row', { name: 'Type No Surah Part Start Date' }).getByRole('checkbox').uncheck();
  await page.getByRole('row', { name: 'page 355 An-Nur' }).first().getByRole('checkbox').check();
  await page.keyboard.down('Shift');
  await page.getByRole('row', { name: 'page 358 An-Nur' }).first().getByRole('checkbox').check();
  await page.keyboard.up('Shift');
  await expect(page.getByRole('row', { name: 'page 355 An-Nur' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: 'page 356 An-Nur' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: 'page 357 An-Nur' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: 'page 358 An-Nur' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: 'page 359 An-Nur' }).getByRole('checkbox').first()).not.toBeChecked();
  // revision page
  await page.getByRole('link', { name: 'Revision' }).click();
  await page.getByRole('row', { name: '358 1 2 ✅ Good 24 An-Nur 18' }).first().getByRole('checkbox').check();
  await page.keyboard.down('Shift');
  await page.getByRole('row', { name: '355 1 2 ✅ Good 24 An-Nur 18' }).first().getByRole('checkbox').check();
  await page.keyboard.up('Shift');
  await expect(page.getByRole('row', { name: '355 1 2 ✅ Good 24 An-Nur 18' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: '356 1 2 ✅ Good 24 An-Nur 18' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: '357 1 2 ✅ Good 24 An-Nur 18' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: '358 1 2 ✅ Good 24 An-Nur 18' }).getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByRole('row', { name: '359 1 2 ✅ Good 24 An-Nur 18' }).getByRole('checkbox').first()).not.toBeChecked();
});


test('started_word_of_the_page', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('2');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('2 - 2 Al-Baqarah - الم ذَلِكَ الْكِتَابُ');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('150');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('150 - 6 Al-An\'am - هَلْ يَنْظُرُونَ إِلَّا');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('300');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('300 - 18 Al-Kahf - وَلَقَدْ صَرَّفْنَا فِي');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('600');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('600 - 100 Al-\'Adiyat - إِنَّ الْإِنْسَانَ لِرَبِّهِ');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('604');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('604 - 112 Al-Ikhlas - قُلْ هُوَ اللَّهُ');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('101');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.locator('tbody')).toContainText('الَّذِينَ يَتَرَبَّصُونَ بِكُمْ');
  await expect(page.locator('tbody')).toContainText('يَاأَهْلَ الْكِتَابِ لَا');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('599');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.locator('h1')).toContainText('599 - 98 Al-Bayyinah => 603 - 109 Al-Kafirun');
  await expect(page.locator('tbody')).toContainText('إِنَّ الَّذِينَ كَفَرُوا');
  await expect(page.locator('tbody')).toContainText('قُلْ يَاأَيُّهَا الْكَافِرُونَ');
});


test('page_exceed', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('900');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page).toHaveURL('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('610');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page).toHaveURL('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('603');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.locator('h1')).toContainText('603 - 109 Al-Kafirun => 604 - 112 Al-Ikhlas');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page).toHaveURL('http://localhost:5001/');
  await expect(page.locator('#main')).toContainText('No further page');
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('2');
});


test('page_feild_with_empty', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await expect(page.getByRole('textbox', { name: 'page' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'page' })).not.toHaveValue('');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).clear();
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page).toHaveURL('http://localhost:5001/');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page).toHaveURL('http://localhost:5001/');
});



test('page_field_fill_with_last_added_page_no', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  // single entry
  await page.getByRole('textbox', { name: 'page' }).fill('410');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('410 - 30 Ar-Rum - وَلَئِنْ أَرْسَلْنَا رِيحًا');
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('410');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.locator('h1')).toContainText('411 - 31 Luqman - الم تِلْكَ آيَاتُ');
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('411');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('411');
  // after bulk entry
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.getByRole('heading', { name: '411 - 31 Luqman => 415' })).toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('416');
});

test('radio_feild_with_empty', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('10');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.getByRole('heading', { name: '10 - 2 Al-Baqarah => 14 - 2' })).toBeVisible();
  await page.getByRole('row', { name: 'page 14 Al-Baqarah' }).getByLabel('✅ Good').uncheck();
  await page.getByRole('row', { name: 'page 13 Al-Baqarah' }).getByLabel('✅ Good').uncheck();
  await page.getByRole('row', { name: 'page 12 Al-Baqarah' }).getByLabel('✅ Good').uncheck();
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('heading', { name: '12 - 2 Al-Baqarah => 16 - 2' })).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL('http://localhost:5001/');
  await page.getByRole('link', { name: 'Revision' }).click();
  await expect(page.getByRole('row', { name: '11 1 2 ✅ Good 2 Al-Baqarah 1' }).first().getByRole('checkbox')).toBeVisible();
  await expect(page.getByRole('row', { name: '10 1 2 ✅ Good 2 Al-Baqarah 1' }).first().getByRole('checkbox')).toBeVisible();
});