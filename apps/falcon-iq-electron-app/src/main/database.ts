import { app } from 'electron';
import Database from 'better-sqlite3';
import path from 'node:path';
import { getLogger } from '@libs/shared/utils/logger';
import { isDevelopment } from '@libs/shared/utils/env';
import type { PythonServerState } from './types/python-server';

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
    CREATE TABLE IF NOT EXISTS python_server (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      pid INTEGER NOT NULL,
      port INTEGER NOT NULL,
      started_at TEXT NOT NULL,
      python_executable TEXT NOT NULL,
      server_script_path TEXT NOT NULL
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

export function savePythonServerState(state: PythonServerState) {
  try {
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO python_server (id, pid, port, started_at, python_executable, server_script_path)
      VALUES (1, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      state.pid,
      state.port,
      state.startedAt,
      state.pythonExecutable,
      state.serverScriptPath
    );
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to save Python server state' };
  }
}

export function getPythonServerState() {
  try {
    const stmt = db.prepare('SELECT * FROM python_server WHERE id = 1');
    const row = stmt.get() as {
      pid: number;
      port: number;
      started_at: string;
      python_executable: string;
      server_script_path: string;
    } | undefined;

    if (!row) {
      return { success: true, data: null };
    }

    return {
      success: true,
      data: {
        pid: row.pid,
        port: row.port,
        startedAt: row.started_at,
        pythonExecutable: row.python_executable,
        serverScriptPath: row.server_script_path,
      },
    };
  } catch {
    return { success: false, error: 'Failed to fetch Python server state' };
  }
}

export function clearPythonServerState() {
  try {
    const stmt = db.prepare('DELETE FROM python_server WHERE id = 1');
    stmt.run();
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to clear Python server state' };
  }
}

export function closeDatabase() {
  if (db) {
    db.close();
  }
}
