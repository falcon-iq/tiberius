import { getDatabase } from './init';

export interface Goal {
  id: number;
  goal: string;
  start_date: string;
  end_date: string | null;
}

export interface AddGoalInput {
  goal: string;
  start_date?: string | null;
  end_date?: string | null;
}

export interface UpdateGoalInput {
  id: number;
  end_date?: string | null;
}

export function getGoals() {
  try {
    const db = getDatabase();
    const stmt = db.prepare('SELECT * FROM goals ORDER BY start_date DESC');
    return { success: true, data: stmt.all() as Goal[] };
  } catch {
    return { success: false, error: 'Failed to fetch goals' };
  }
}

export function addGoal(input: AddGoalInput) {
  try {
    const db = getDatabase();
    const insertStmt = db.prepare(`
      INSERT INTO goals (goal, start_date, end_date)
      VALUES (?, ?, ?)
    `);
    const result = insertStmt.run(
      input.goal,
      input.start_date ?? null,
      input.end_date ?? null
    );

    // Fetch the complete record including start_date
    const selectStmt = db.prepare('SELECT * FROM goals WHERE id = ?');
    const goal = selectStmt.get(result.lastInsertRowid) as Goal;

    return {
      success: true,
      data: goal
    };
  } catch {
    return { success: false, error: 'Failed to add goal' };
  }
}

export function deleteGoal(id: number) {
  try {
    const db = getDatabase();
    const stmt = db.prepare('DELETE FROM goals WHERE id = ?');
    stmt.run(id);
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to delete goal' };
  }
}

export function updateGoal(input: UpdateGoalInput) {
  try {
    const db = getDatabase();
    const stmt = db.prepare(`
      UPDATE goals
      SET end_date = ?
      WHERE id = ?
    `);
    stmt.run(input.end_date ?? null, input.id);
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to update goal' };
  }
}

export function getEarliestOpenGoalTimestamp() {
  try {
    const db = getDatabase();
    const stmt = db.prepare(`
      SELECT MIN(start_date) as earliest_date
      FROM goals
      WHERE end_date IS NULL
    `);
    const result = stmt.get() as { earliest_date: string | null };
    return { success: true, data: result.earliest_date };
  } catch {
    return { success: false, error: 'Failed to get earliest goal timestamp' };
  }
}
