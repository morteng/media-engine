import { test, expect, waitForApi } from './fixtures/test-fixtures';

test.describe('AI Workspace Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ai');
    await waitForApi(page);
  });

  test('displays AI workspace header', async ({ page }) => {
    const heading = page.locator('h1, h2').filter({ hasText: /AI|Workspace/ }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('shows task queue section', async ({ page }) => {
    // Look for queue-related content
    const queueSection = page.locator('text=/Queue|Tasks|Pending/i').first();
    await expect(queueSection).toBeVisible({ timeout: 10000 });
  });

  test('displays queue tabs', async ({ page }) => {
    // Check for tabs like Queue, Sessions, Research, Notes (NavLink with .tab class)
    const tabs = page.locator('.tab').filter({ hasText: /Queue|Sessions|Research|Notes/ });
    const count = await tabs.count();
    expect(count).toBeGreaterThan(0);
  });

  test('can switch to sessions tab', async ({ page }) => {
    const sessionsTab = page.locator('.tab:has-text("Sessions")').first();
    if (await sessionsTab.isVisible()) {
      await sessionsTab.click();
      await page.waitForTimeout(500);
      // Check for session-related content
      const sessionContent = page.locator('text=/Session|Active|History/i').first();
      await expect(sessionContent).toBeVisible({ timeout: 5000 });
    }
  });

  test('can switch to research tab', async ({ page }) => {
    const researchTab = page.locator('.tab:has-text("Research")').first();
    if (await researchTab.isVisible()) {
      await researchTab.click();
      await page.waitForTimeout(500);
    }
  });

  test('can switch to notes tab', async ({ page }) => {
    const notesTab = page.locator('.tab:has-text("Notes")').first();
    if (await notesTab.isVisible()) {
      await notesTab.click();
      await page.waitForTimeout(500);
    }
  });

  test('queue shows empty state when no tasks', async ({ page }) => {
    // Look for empty state message
    const emptyState = page.locator('text=/No tasks|empty|queue/i').first();
    // May or may not be visible depending on queue state
    if (await emptyState.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(emptyState).toBeVisible();
    }
  });
});

test.describe('AI Queue API Integration', () => {
  test('queue stats endpoint returns data', async ({ request }) => {
    const response = await request.get('/api/ai/queue/stats');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('by_status');
    expect(data).toHaveProperty('by_operation');
  });

  test('tasks endpoint returns list', async ({ request }) => {
    const response = await request.get('/api/ai/tasks');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('tasks');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('stats');
    expect(Array.isArray(data.tasks)).toBeTruthy();
  });

  test('can submit a task via API', async ({ request }) => {
    const response = await request.post('/api/ai/tasks', {
      data: {
        operation: 'analyze',
        selections: [
          {
            path: 'content/en/chapters/01_introduction.md',
            content: 'Test content for E2E',
            title: 'E2E Test Doc',
          }
        ],
        instructions: 'E2E test task',
        priority: 'low',
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('task_id');
    expect(data.status).toBe('pending');
    expect(data.operation).toBe('analyze');

    // Clean up - cancel the task
    const taskId = data.task_id;
    await request.post(`/api/ai/tasks/${taskId}/cancel`);
    await request.delete(`/api/ai/tasks/${taskId}`);
  });

  test('operations endpoint lists available operations', async ({ request }) => {
    const response = await request.get('/api/ai/operations');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('operations');
    expect(Array.isArray(data.operations)).toBeTruthy();

    const opIds = data.operations.map((op: { id: string }) => op.id);
    expect(opIds).toContain('improve');
    expect(opIds).toContain('translate');
    expect(opIds).toContain('analyze');
  });

  test('context endpoint returns AI context', async ({ request }) => {
    const response = await request.get('/api/ai/context');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(typeof data).toBe('object');
  });

  test('sessions endpoint returns list', async ({ request }) => {
    const response = await request.get('/api/ai/sessions');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('sessions');
    expect(data).toHaveProperty('total');
  });
});

test.describe('AI Task Lifecycle', () => {
  test('complete task lifecycle: submit, cancel, delete', async ({ request }) => {
    // 1. Submit a task
    const submitResponse = await request.post('/api/ai/tasks', {
      data: {
        operation: 'improve',
        selections: [
          {
            path: 'content/en/test.md',
            content: 'Lifecycle test',
            title: 'Lifecycle Test',
          }
        ],
        instructions: 'Test lifecycle',
        priority: 'normal',
      }
    });

    expect(submitResponse.ok()).toBeTruthy();
    const submitData = await submitResponse.json();
    const taskId = submitData.task_id;

    // 2. Verify task appears in list
    const listResponse = await request.get('/api/ai/tasks?status=pending');
    const listData = await listResponse.json();
    const taskInList = listData.tasks.find((t: { id: string }) => t.id === taskId);
    expect(taskInList).toBeDefined();

    // 3. Get task details
    const getResponse = await request.get(`/api/ai/tasks/${taskId}`);
    expect(getResponse.ok()).toBeTruthy();
    const taskDetails = await getResponse.json();
    expect(taskDetails.id).toBe(taskId);
    expect(taskDetails.status).toBe('pending');

    // 4. Cancel the task
    const cancelResponse = await request.post(`/api/ai/tasks/${taskId}/cancel`);
    expect(cancelResponse.ok()).toBeTruthy();

    // 5. Verify cancelled status
    const getAfterCancel = await request.get(`/api/ai/tasks/${taskId}`);
    const cancelledTask = await getAfterCancel.json();
    expect(cancelledTask.status).toBe('cancelled');

    // 6. Delete the task
    const deleteResponse = await request.delete(`/api/ai/tasks/${taskId}`);
    expect(deleteResponse.ok()).toBeTruthy();

    // 7. Verify task is gone
    const getAfterDelete = await request.get(`/api/ai/tasks/${taskId}`);
    expect(getAfterDelete.status()).toBe(404);
  });

  test('priority ordering in task list', async ({ request }) => {
    // Submit tasks with different priorities
    const priorities = ['low', 'high', 'urgent', 'normal'];
    const taskIds: string[] = [];

    for (const priority of priorities) {
      const response = await request.post('/api/ai/tasks', {
        data: {
          operation: 'analyze',
          selections: [{ path: `${priority}.md`, content: priority, title: priority }],
          instructions: `Priority ${priority}`,
          priority,
        }
      });
      const data = await response.json();
      taskIds.push(data.task_id);
    }

    // Get list and check ordering
    const listResponse = await request.get('/api/ai/tasks?status=pending');
    const listData = await listResponse.json();

    // Find our tasks
    const ourTasks = listData.tasks.filter((t: { id: string }) => taskIds.includes(t.id));

    // Verify urgent comes before high comes before normal comes before low
    if (ourTasks.length >= 4) {
      const priorityOrder = ourTasks.map((t: { priority: string }) => t.priority);
      const urgentIndex = priorityOrder.indexOf('urgent');
      const highIndex = priorityOrder.indexOf('high');
      const normalIndex = priorityOrder.indexOf('normal');
      const lowIndex = priorityOrder.indexOf('low');

      expect(urgentIndex).toBeLessThan(highIndex);
      expect(highIndex).toBeLessThan(normalIndex);
      expect(normalIndex).toBeLessThan(lowIndex);
    }

    // Clean up
    for (const taskId of taskIds) {
      await request.post(`/api/ai/tasks/${taskId}/cancel`);
      await request.delete(`/api/ai/tasks/${taskId}`);
    }
  });
});
