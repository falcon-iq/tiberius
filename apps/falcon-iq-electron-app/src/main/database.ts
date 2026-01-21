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

  // Create table if it doesn't exist
  db.exec(`
    CREATE TABLE IF NOT EXISTS github_users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE
    )
  `);

  log.info('Database initialized successfully');
}

export function getGithubUsers() {
  try {
    const stmt = db.prepare('SELECT * FROM github_users ORDER BY username');
    return { success: true, data: stmt.all() };
  } catch {
    return { success: false, error: 'Failed to fetch users' };
  }
}

export function addGithubUser(username: string) {
  try {
    const stmt = db.prepare('INSERT INTO github_users (username) VALUES (?)');
    const result = stmt.run(username);
    return { success: true, data: { id: result.lastInsertRowid, username } };
  } catch (error) {
    if ((error as Error).message.includes('UNIQUE constraint')) {
      return { success: false, error: 'Username already exists' };
    }
    return { success: false, error: 'Failed to add user' };
  }
}

export function deleteGithubUser(id: number) {
  try {
    const stmt = db.prepare('DELETE FROM github_users WHERE id = ?');
    stmt.run(id);
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to delete user' };
  }
}

export function closeDatabase() {
  if (db) {
    db.close();
  }
}
