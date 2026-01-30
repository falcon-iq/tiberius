import { app } from 'electron';
import Database from 'better-sqlite3';
import path from 'node:path';
import { getLogger } from '@libs/shared/utils/logger';
import { isDevelopment } from '@libs/shared/utils/env';

const log = getLogger({ name: 'database' });

let db: Database.Database;

export function getDatabase(): Database.Database {
  if (!db) {
    throw new Error('Database not initialized. Call initDatabase() first.');
  }
  return db;
}

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

export function closeDatabase() {
  if (db) {
    db.close();
  }
}
