import { test, expect } from '@playwright/test';

// #TODO: During run all test, few test fails sometimes, need to figure out why.

// dymamically get the current date
const now = new Date();
const currentDate = now.toISOString().split('T')[0];

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
  await expect(page.locator('h1')).toContainText('3 - 2 Al Baqara - إِنَّ الَّذِينَ كَفَرُوا');
  await expect(page.getByRole('button', { name: 'SRS' })).toBeVisible();
  await page.locator('body').press('Tab');
  await expect(page.getByRole('spinbutton', { name: 'Plan ID' })).toHaveValue('1');
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate); 
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('3');
  await expect(page.getByText('Rating ✅ Good 😄 Ok ❌ Bad')).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.locator('#main')).toContainText('2 - 2 Al Baqara Start');
});

test('bulk_entry', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('3');
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.locator('h1')).toContainText('3 - 2 Al Baqara => 7 - 2 Al Baqara');
  await expect(page.getByRole('textbox', { name: 'Revision Date' })).toHaveValue(currentDate); 
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.locator('a').filter({ hasText: 'New Memorization' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).fill('1');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('heading', { name: '8 - 2 Al Baqara => 12 - 2' })).toBeVisible();
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
  await expect(page.locator('h1')).toContainText('99 - 4 An Nisa => 100 - 4 An Nisa');
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
  await page.getByRole('row', { name: '99 1 1 ✅ Good 4 An Nisa Juz' }).getByRole('checkbox').check();
  await page.getByRole('row', { name: '100 1 1 ✅ Good 4 An Nisa Juz' }).getByRole('checkbox').check();
  await expect(page.getByRole('button',{name:'Bulk Edit'})).toBeEnabled();
  await expect(page.getByRole('button',{name:'Bulk Delete'})).toBeEnabled();
  await page.getByRole('button', { name: 'Bulk Edit' }).click();
  await page.getByRole('row', { name: `100 ${currentDate} 1 1 ✅ Good 😄` }).getByLabel('❌ Bad').check();
  await page.getByRole('row', { name: `99 ${currentDate} 1 1 ✅ Good 😄` }).getByLabel('❌ Bad').check();
  await page.getByRole('textbox', { name: 'Revision Date' }).fill('2025-04-20');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page).toHaveURL("http://localhost:5001/revision");
  await expect(page.getByRole('row', { name: '100 1 1 ❌ Bad 4 An Nisa Juz' }).getByRole('checkbox')).toBeVisible();
  await expect(page.getByRole('row', { name: '99 1 1 ❌ Bad 4 An Nisa Juz 5' }).getByRole('checkbox')).toBeVisible();
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
 await expect(page.getByRole('heading', { name: '38 - 2 Al Baqara => 42 - Juz' })).toBeVisible();
 await page.getByRole('button', { name: 'Cancel' }).click();
 await expect(page).toHaveURL("http://localhost:5001/");
//  bulk edit from revision range
 await page.getByRole('link', { name: '- 2 Al Baqara -> 37 - 2 Al Baqara' }).click();
 await page.getByRole('button', { name: 'Cancel' }).click();
 await expect(page).toHaveURL("http://localhost:5001/");
 await page.getByRole('link', { name: '- 2 Al Baqara -> 37 - 2 Al Baqara' }).click();
 await page.getByRole('row', { name: `33 ${currentDate} 1 1 ✅ Good 😄` }).getByLabel('😄 Ok').check();
 await page.getByRole('row', { name: `34 ${currentDate} 1 1 ✅ Good 😄` }).getByLabel('😄 Ok').check();
 await page.getByRole('row', { name: `35 ${currentDate} 1 1 ✅ Good 😄` }).getByLabel('😄 Ok').check();
 await page.getByRole('button', { name: 'Save' }).click();
 expect(page.url()).toContain("http://localhost:5001/revision/bulk_edit?ids=");
});



test('continue_with_bulk_add', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('55');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await page.locator('uk-select[name="mode_id"] >> button.uk-input-fake').first().click();
  await page.locator('uk-select[name="mode_id"]  >> a').filter({ hasText: 'SEQ' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).click();
  await page.getByRole('spinbutton', { name: 'Plan Id' }).fill('1');
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await page.getByRole('link', { name: 'Quran SRS' }).click();
  //enable continue with bulk add
  await expect(page.getByText('56 - 3 Aal-e-Imran')).toBeVisible();
  await page.getByRole('link', { name: '56 - 3 Aal-e-Imran' }).click();
  await page.getByRole('button', { name: 'Save' }).click();
  expect(page.url()).toContain("mode_id=1");
  expect(page.url()).toContain("plan_id=1");
  await page.getByRole('button', { name: 'Cancel' }).click();
  expect(page.url()).toContain("http://localhost:5001/revision/bulk_add?page=61" );
  await expect(page.getByRole('link', { name: '61 - Juz 3 End' })).toBeVisible();
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
  await page.getByRole('row', { name: '66 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox').check();
  await page.getByRole('row', { name: '67 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox').check();
  await page.getByRole('row', { name: '68 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox').check();
  await page.getByRole('row', { name: '69 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox').check();
  await page.getByRole('row', { name: '70 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox').check();
  page.on('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Bulk Delete' }).click();
  await expect(page.getByRole('row', { name: '66 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: '67 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: '68 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: '69 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox')).not.toBeVisible();
  await expect(page.getByRole('row', { name: '70 1 1 ✅ Good 3 Aal-e-Imran' }).getByRole('checkbox')).not.toBeVisible();
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
  await expect(page.getByRole('heading', { name: '155 - 7 Al A\'raf => 164 - 7 Al A\'raf' })).toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();
  expect(page.url()).toContain("http://localhost:5001/revision/bulk_add?page=");
  await expect(page.getByRole('heading', { name: '165 - 7 Al A\'raf => 174 - 7' })).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.getByText('155 - 7 Al A\'raf').first()).toBeVisible();
});


test('single_add_with_custom_range', async ({ page }) => {
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('255.10');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).click();
  await page.getByRole('spinbutton', { name: 'Plan ID' }).fill('3');
  await expect(page.getByRole('heading', { name: '255 - 14 Ibrahim Start' })).toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();
  expect(page.url()).toContain("http://localhost:5001/revision/add?page=");
  await expect(page.getByRole('heading', { name: '256 - 14 Ibrahim' })).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page).toHaveURL("http://localhost:5001/");
  await expect(page.getByText('255 - 14 Ibrahim Start').first()).toBeVisible();
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
  await page.getByRole('link', { name: '- 24 Nur -> 359 - 25 Furqan Start' }).click();
  await page.getByRole('row', { name: 'Page Date Mode Plan ID Rating' }).getByRole('checkbox').uncheck();
  await page.getByRole('row', { name: `355 ${currentDate} 1 2 ✅ Good 😄` }).getByRole('checkbox').check();
  await page.keyboard.down('Shift');
  await page.getByRole('row', { name: `358 ${currentDate} 1 2 ✅ Good 😄` }).getByRole('checkbox').check();
  await page.keyboard.up('Shift');
  await expect(page.getByRole('row', { name: `355 ${currentDate} 1 2 ✅ Good 😄` }).getByRole('checkbox')).toBeChecked();
  await expect(page.getByRole('row', { name: `356 ${currentDate} 1 2 ✅ Good 😄` }).getByRole('checkbox')).toBeChecked();
  await expect(page.getByRole('row', { name: `357 ${currentDate} 1 2 ✅ Good 😄` }).getByRole('checkbox')).toBeChecked();
  await expect(page.getByRole('row', { name: `358 ${currentDate} 1 2 ✅ Good 😄` }).getByRole('checkbox')).toBeChecked();
  await expect(page.getByRole('row', { name: `359 ${currentDate} 1 2 ✅ Good 😄` }).getByRole('checkbox')).not.toBeChecked();
});


test('started_word_of_the_page', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('2');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('2 - 2 Al Baqara Start - الم ذَلِكَ الْكِتَابُ');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('150');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('150 - 6 Al An\'am End - هَلْ يَنْظُرُونَ إِلَّا');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('300');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('300 - 18 Kahf - وَلَقَدْ صَرَّفْنَا فِي');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('600');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('600 - 101 Qari\'ah Start - إِنَّ الْإِنْسَانَ لِرَبِّهِ');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('textbox', { name: 'page' }).click();
  await page.getByRole('textbox', { name: 'page' }).fill('604');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('604 - 112 Ikhlas Start - قُلْ هُوَ اللَّهُ');
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
  await expect(page.locator('h1')).toContainText('599 - 99 Zalzalah Start => 603 - 109 Kafirun Start');
  await expect(page.locator('tbody')).toContainText('إِنَّ الَّذِينَ كَفَرُوا');
  await expect(page.locator('tbody')).toContainText('قُلْ يَاأَيُّهَا الْكَافِرُونَ');
});


test('page_field_fill_with_last_added_page_no', async ({ page }) => {  
  // Recording...
  await page.goto('http://localhost:5001/');
  await page.getByRole('textbox', { name: 'page' }).click();
  // single entry
  await page.getByRole('textbox', { name: 'page' }).fill('410');
  await page.getByRole('button', { name: 'Single Entry' }).click();
  await expect(page.locator('h1')).toContainText('410 - 30 Rum End - وَلَئِنْ أَرْسَلْنَا رِيحًا');
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('410');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.locator('h1')).toContainText('411 - 31 Luqman Start - الم تِلْكَ آيَاتُ');
  await expect(page.getByRole('spinbutton', { name: 'Page' })).toHaveValue('411');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('411');
  // after bulk entry
  await page.getByRole('button', { name: 'Bulk Entry' }).click();
  await expect(page.getByRole('heading', { name: '411 - 31 Luqman Start => 415' })).toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('textbox', { name: 'page' })).toHaveValue('416');
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
  await expect(page.locator('h1')).toContainText('603 - 109 Kafirun Start => 604 - 112 Ikhlas Start');
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


