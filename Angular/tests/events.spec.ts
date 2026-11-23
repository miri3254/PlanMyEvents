import { expect, Page, test } from '@playwright/test';

const BASE_URL = process.env['PLANMYEVENTS_BASE_URL'] ?? 'http://localhost:4200';

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
    status: 'מחכה לאישור',
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
    status: 'מאושר',
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
    status: 'בוטל',
    notes: 'בדיקות אוטומטיות'
  }
];

const toApiEvent = (event: SeedEvent, index: number) => ({
  id: index + 1000,
  name: event.name,
  guest_count: event.participants,
  event_category: event.eventType,
  menu_type: event.foodType,
  date: event.eventDate,
  status: event.status,
  notes: event.notes,
  dishes: [],
  owners: [],
  created_at: event.createdAt,
  updated_at: event.createdAt
});

async function mockEventsApi(page: Page) {
  const events = seededEvents.map(toApiEvent);
  await page.route(/\/api\/events(?:\?.*)?$/, async route => {
    const request = route.request();
    if (request.method() === 'POST') {
      const payload = request.postDataJSON();
      const created = {
        ...payload,
        id: events.length + 1000,
        dishes: [],
        owners: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      events.push(created);
      await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(created) });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: events, total: events.length, skip: 0, limit: 100 })
    });
  });
}

async function openEventsPage(page: Page) {
  await mockEventsApi(page);
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
    await expect(page.getByLabel('רשימת אירועים').getByText('אירוע מבוטל')).toBeVisible();
  });

  test('filters cancelled events', async ({ page }) => {
    await page.getByRole('button', { name: 'אירועים שהתבטלו' }).click();
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await expect(page.getByLabel('רשימת אירועים').getByText('אירוע מבוטל')).toBeVisible();
    await expect(page.getByText('אירוע מאושר')).not.toBeVisible();
  });

  test('opens event details from the list', async ({ page }) => {
    const row = page.getByRole('row', { name: /אירוע מאושר/ });
    await row.getByRole('button', { name: 'פרטים' }).click();
    const detailDialog = page.getByRole('dialog').filter({ hasText: 'פרטי אירוע - אירוע מאושר' });
    await expect(detailDialog).toBeVisible();
    await expect(detailDialog.getByText('אירוע מאושר', { exact: true })).toBeVisible();
  });

  test('creates a new event from the dialog', async ({ page }) => {
    await page.getByRole('main').getByRole('button', { name: 'אירוע חדש' }).click();
    const dialog = page.getByRole('dialog').filter({ hasText: 'אירוע חדש' });
    await expect(dialog).toBeVisible();

    // Fill Name
    await dialog.locator('input.p-inputtext').first().fill('אירוע אוטומציה');

    // Fill Participants
    await dialog.locator('p-inputnumber input').first().fill('50');

    // Save
    await dialog.getByRole('button', { name: 'שמירת אירוע' }).click();

    await expect(dialog).toBeHidden();
    await expect(page.getByLabel('רשימת אירועים').getByText('אירוע אוטומציה')).toBeVisible();
  });
});
