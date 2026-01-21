import { expect, Page, test } from '@playwright/test';

const BASE_URL = process.env['PLANMYEVENTS_BASE_URL'] ?? 'http://localhost:4200';
const STORAGE_PREFIX = 'planmyevents_';

type SeedEvent = {
  id: string;
  name: string;
  participants: number;
  eventType: string;
  foodType: string;
  dishes: { dishId: string; quantity: number }[];
  createdAt: string;
  eventDate: string;
  status: string;
  notes: string;
};

const dateInDays = (days: number): string => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  date.setHours(0, 0, 0, 0);
  return date.toISOString();
};

const seededEvents: SeedEvent[] = [
  {
    id: 'evt-pending',
    name: 'אירוע בהמתנה',
    participants: 80,
    eventType: 'שבת',
    foodType: 'חלבי',
    dishes: [],
    createdAt: new Date().toISOString(),
    eventDate: dateInDays(30),
    status: 'בהמתנה לאישור',
    notes: 'בדיקות אוטומטיות'
  },
  {
    id: 'evt-approved',
    name: 'אירוע מאושר',
    participants: 120,
    eventType: 'ברית',
    foodType: 'בשרי',
    dishes: [],
    createdAt: new Date().toISOString(),
    eventDate: dateInDays(60),
    status: 'אושר',
    notes: 'בדיקות אוטומטיות'
  },
  {
    id: 'evt-cancelled',
    name: 'אירוע מבוטל',
    participants: 40,
    eventType: 'בוקר',
    foodType: 'פרווה',
    dishes: [],
    createdAt: new Date().toISOString(),
    eventDate: dateInDays(-10),
    status: 'התבטל',
    notes: 'בדיקות אוטומטיות'
  }
];

async function seedLocalStorage(page: Page) {
  await page.addInitScript(
    ({ events, prefix }) => {
      localStorage.setItem(`${prefix}events`, JSON.stringify(events));
      localStorage.setItem(`${prefix}currentEvent`, events[0]?.id ?? '');
      localStorage.removeItem(`${prefix}cart`);
    },
    { events: seededEvents, prefix: STORAGE_PREFIX }
  );
}

async function openEventsPage(page: Page) {
  await seedLocalStorage(page);
  await page.goto(`${BASE_URL}/events`);
  await expect(page.getByRole('heading', { name: 'אירועים' })).toBeVisible();
}

test.describe('Events page', () => {
  test.beforeEach(async ({ page }) => {
    await openEventsPage(page);
  });

  test('shows seeded events in the list', async ({ page }) => {
    await expect(page.locator('tbody tr')).toHaveCount(3);
    await expect(page.getByText('אירוע בהמתנה')).toBeVisible();
    await expect(page.getByText('אירוע מאושר')).toBeVisible();
    await expect(page.getByText('אירוע מבוטל')).toBeVisible();
  });

  test('filters pending events', async ({ page }) => {
    await page.getByRole('button', { name: 'ממתינים לאישור' }).click();
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await expect(page.getByText('אירוע בהמתנה')).toBeVisible();
    await expect(page.getByText('אירוע מאושר')).not.toBeVisible();
  });

  test('opens event details from the list', async ({ page }) => {
    const row = page.getByRole('row', { name: /אירוע מאושר/ });
    await row.getByRole('button', { name: 'פרטים' }).click();
    // The dialog title for editing is 'עריכת אירוע'
    await expect(page.getByRole('dialog', { name: 'עריכת אירוע' })).toBeVisible();
    // Check that the event name is populated in the input
    await expect(page.locator('input.p-inputtext').first()).toHaveValue('אירוע מאושר');
  });

  test('creates a new event from the dialog', async ({ page }) => {
    await page.getByRole('button', { name: 'אירוע חדש' }).click();
    const dialog = page.getByRole('dialog', { name: 'אירוע חדש' });
    await expect(dialog).toBeVisible();

    // Fill Name
    await dialog.locator('input.p-inputtext').first().fill('אירוע אוטומציה');

    // Fill Participants
    await dialog.locator('p-inputnumber input').fill('50');

    // Select Event Type (first p-select)
    await dialog.locator('p-select').nth(0).click();
    await page.getByRole('option').first().click();

    // Select Food Type (second p-select)
    await dialog.locator('p-select').nth(1).click();
    await page.getByRole('option').first().click();

    // Select Date (p-datepicker)
    // We click the input to open the calendar, then pick "Today"
    await dialog.locator('p-datepicker input').click();
    await page.locator('.p-datepicker-today').click();

    // Save
    await dialog.getByRole('button', { name: 'שמירת אירוע' }).click();

    await expect(dialog).toBeHidden();
    await expect(page.getByText('אירוע אוטומציה')).toBeVisible();
  });
});