import { getDatabase } from './init';

export interface User {
  id: number;
  username: string;
  github_suffix: string | null;
  email_address: string | null;
  firstname: string | null;
  lastname: string | null;
}

export interface AddUserInput {
  username: string;
  github_suffix?: string | null;
  email_address?: string | null;
  firstname?: string | null;
  lastname?: string | null;
}

export function getUsers() {
  try {
    const db = getDatabase();
    const stmt = db.prepare('SELECT * FROM users ORDER BY username');
    return { success: true, data: stmt.all() as User[] };
  } catch {
    return { success: false, error: 'Failed to fetch users' };
  }
}

export function addUser(user: AddUserInput) {
  try {
    const db = getDatabase();
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
      } as User
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
    const db = getDatabase();
    const stmt = db.prepare('DELETE FROM users WHERE id = ?');
    stmt.run(id);
    return { success: true };
  } catch {
    return { success: false, error: 'Failed to delete user' };
  }
}
