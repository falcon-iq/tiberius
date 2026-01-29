import { app } from 'electron';
import Database from 'better-sqlite3';
import path from 'node:path';
import { getLogger } from '@libs/shared/utils/logger';
import { isDevelopment } from '@libs/shared/utils/env';

const log = getLogger({ name: 'database' });

let db: Database.Database;

export function initDatabase() {
  const userDataPath = app.getPath('userData');
  const dbName = isDevelopment() ? 'database.dev.db' : 'database.db';
  const dbPath = path.join(userDataPath, dbName);

  log.info({ dbPath }, 'Initializing database');

  db = new Database(dbPath);

  // Create tables if they don't exist
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE,
      github_suffix TEXT,
      email_address TEXT UNIQUE CHECK (email_address IS NULL OR email_address LIKE '%_@_%._%'),
      firstname TEXT,
      lastname TEXT
    )
  `);

  db.exec(`
    CREATE TABLE IF NOT EXISTS goals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      goal TEXT NOT NULL,
      start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      end_date TIMESTAMP NULL
    )
  `);

  db.exec(`
    CREATE TABLE IF NOT EXISTS pr_stats (
      username TEXT NOT NULL,
      pr_id INTEGER NOT NULL,
      reviewed_authored TEXT NOT NULL CHECK(reviewed_authored IN ('authored', 'reviewed')),
      goal_id INTEGER,
      category TEXT,
      created_time TIMESTAMP,
      confidence REAL,
      author_of_pr TEXT,
      repo TEXT,
      is_ai_author INTEGER CHECK(is_ai_author IN (0, 1)),
      PRIMARY KEY (username, pr_id, reviewed_authored),
      FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
    )
  `);

  db.exec(`
    CREATE TABLE IF NOT EXISTS pr_comment_details (
      pr_number INTEGER NOT NULL,
      comment_id INTEGER NOT NULL,
      username TEXT NOT NULL,
      comment_type TEXT,
      created_at TIMESTAMP,
      is_reviewer INTEGER CHECK(is_reviewer IN (0, 1)),
      line INTEGER,
      side TEXT,
      pr_author TEXT,
      primary_category TEXT,
      secondary_categories TEXT,
      severity TEXT,
      confidence REAL,
      actionability TEXT,
      rationale TEXT,
      is_ai_reviewer INTEGER CHECK(is_ai_reviewer IN (0, 1)),
      is_nitpick INTEGER CHECK(is_nitpick IN (0, 1)),
      mentions_tests INTEGER CHECK(mentions_tests IN (0, 1)),
      mentions_bug INTEGER CHECK(mentions_bug IN (0, 1)),
      mentions_design INTEGER CHECK(mentions_design IN (0, 1)),
      mentions_performance INTEGER CHECK(mentions_performance IN (0, 1)),
      mentions_reliability INTEGER CHECK(mentions_reliability IN (0, 1)),
      mentions_security INTEGER CHECK(mentions_security IN (0, 1)),
      PRIMARY KEY (pr_number, comment_id, username)
    )
  `);

  log.info('Database initialized successfully');
}

export function getUsers() {
  try {
    const stmt = db.prepare('SELECT * FROM users ORDER BY username');
    return { success: true, data: stmt.all() };
  } catch {
    return { success: false, error: 'Failed to fetch users' };
  }
}

export interface AddUserInput {
  username: string;
  github_suffix?: string | null;
  email_address?: string | null;
  firstname?: string | null;
  lastname?: string | null;
}

export function addUser(user: AddUserInput) {
  try {
    const stmt = db.prepare(`
      INSERT INTO users (username, github_suffix, email_address, firstname, lastname)
      VALUES (?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      user.username,
      user.github_suffix ?? null,
      user.email_address ?? null,
      user.firstname ?? null,
      user.lastname ?? null
    );
    return {
      success: true,
      data: {
        id: result.lastInsertRowid,
        ...user
      }
    };
  } catch (error) {
    const errorMessage = (error as Error).message;
    if (errorMessage.includes('UNIQUE constraint')) {
      if (errorMessage.includes('username')) {
        return { success: false, error: 'Username already exists' };
      }
      if (errorMessage.includes('email_address')) {
        return { success: false, error: 'Email address already exists' };
      }
      return { success: false, error: 'Duplicate entry' };
    }
    if (errorMessage.includes('CHECK constraint')) {
      return { success: false, error: 'Invalid email address format' };
    }
    return { success: false, error: 'Failed to add user' };
  }
}

export function deleteUser(id: number) {
  try {
    const stmt = db.prepare('DELETE FROM users WHERE id = ?');
    stmt.run(id);
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to delete user' };
  }
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

export interface Goal {
  id: number;
  goal: string;
  start_date: string;
  end_date: string | null;
}

export function getGoals() {
  try {
    const stmt = db.prepare('SELECT * FROM goals ORDER BY start_date DESC');
    return { success: true, data: stmt.all() };
  } catch {
    return { success: false, error: 'Failed to fetch goals' };
  }
}

export function addGoal(input: AddGoalInput) {
  try {
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
    const stmt = db.prepare('DELETE FROM goals WHERE id = ?');
    stmt.run(id);
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to delete goal' };
  }
}

export function updateGoal(input: UpdateGoalInput) {
  try {
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

export function closeDatabase() {
  if (db) {
    db.close();
  }
}
