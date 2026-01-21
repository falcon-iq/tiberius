# Database Usage Example

## How to use the GitHub Users database in your React components

```tsx
import { useEffect, useState } from 'react';
import type { GithubUser } from '../types/electron';

function ExampleComponent() {
  const [users, setUsers] = useState<GithubUser[]>([]);
  const [error, setError] = useState<string>('');
  const [username, setUsername] = useState('');

  // Load users on mount
  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers() {
    const result = await window.api.getGithubUsers();
    if (result.success && result.data) {
      setUsers(result.data);
      setError('');
    } else {
      setError(result.error || 'Failed to load users');
    }
  }

  async function handleAddUser() {
    if (!username.trim()) return;
    
    const result = await window.api.addGithubUser(username);
    if (result.success) {
      setUsername('');
      loadUsers(); // Refresh the list
    } else {
      setError(result.error || 'Failed to add user');
    }
  }

  async function handleDeleteUser(id: number) {
    const result = await window.api.deleteGithubUser(id);
    if (result.success) {
      loadUsers(); // Refresh the list
    } else {
      setError(result.error || 'Failed to delete user');
    }
  }

  return (
    <div>
      <h1>GitHub Users</h1>
      
      {error && <div style={{ color: 'red' }}>{error}</div>}
      
      <div>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter GitHub username"
        />
        <button onClick={handleAddUser}>Add User</button>
      </div>

      <ul>
        {users.map((user) => (
          <li key={user.id}>
            {user.username}
            <button onClick={() => handleDeleteUser(user.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## Available API Methods

All methods return a `DatabaseResult<T>` object with this structure:

```typescript
{
  success: boolean;
  data?: T;        // Present if success is true
  error?: string;  // Present if success is false (user-friendly message)
}
```

### `window.api.getGithubUsers()`
Returns all GitHub users from the database.

```typescript
const result = await window.api.getGithubUsers();
// result.data is GithubUser[] if successful
```

### `window.api.addGithubUser(username: string)`
Adds a new GitHub user. Returns error if username already exists.

```typescript
const result = await window.api.addGithubUser('octocat');
// result.data is the created user object if successful
```

### `window.api.deleteGithubUser(id: number)`
Deletes a user by their ID.

```typescript
const result = await window.api.deleteGithubUser(1);
// result.success is true if deleted
```

## Database Location

The database is stored at:
- **macOS**: `~/Library/Application Support/falcon-iq-electron-app/database.db`
- **Windows**: `%APPDATA%/falcon-iq-electron-app/database.db`
- **Linux**: `~/.config/falcon-iq-electron-app/database.db`

Check your console for the exact path when the app starts!
