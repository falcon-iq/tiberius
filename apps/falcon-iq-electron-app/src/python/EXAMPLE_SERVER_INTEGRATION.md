# Example: Using prDataReader from server.py

This document shows how to integrate `prDataReader.py` functions into FastAPI endpoints in `server.py`.

## How It Works

When `server.py` starts, it sets the `FALCON_BASE_DIR` environment variable **before** any imports:

```python
# server.py (lines 1-10)
import sys
import os

# CRITICAL: Set environment variables BEFORE any imports
if len(sys.argv) > 2:
    os.environ['FALCON_BASE_DIR'] = sys.argv[2]
if len(sys.argv) > 3:
    os.environ['FALCON_IS_DEV'] = '1' if sys.argv[3].lower() == 'true' else '0'
```

This means that when you import `prDataReader` later, it will automatically use the correct base directory from the environment variable. **No additional setup needed!**

## Example Endpoints

### 1. Get PR Details

Add this to `server.py`:

```python
import sqlite3
from prDataReader import get_pr_details, get_comment_details, get_pr_files
from common import getDBPath, get_base_dir

@app.get("/api/pr/{pr_id}")
def get_pr(pr_id: int, username: Optional[str] = None):
    """
    Get PR details by PR ID.
    
    Args:
        pr_id: PR number
        username: Optional username filter
    
    Returns:
        PR details dictionary or error
    """
    try:
        # Get base directory (uses FALCON_BASE_DIR env var set by server.py)
        base_dir = get_base_dir()
        
        # Connect to database
        db_path = getDBPath(base_dir)
        if not db_path.exists():
            return {"error": f"Database not found: {db_path}"}
        
        db_conn = sqlite3.connect(str(db_path))
        
        # Get PR details
        pr_details = get_pr_details(db_conn, pr_id=pr_id, username=username)
        
        db_conn.close()
        
        if pr_details:
            return {"success": True, "data": pr_details}
        else:
            return {"success": False, "error": f"PR {pr_id} not found"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 2. Get Comment Details

```python
@app.get("/api/pr/{pr_id}/comment/{comment_id}")
def get_comment(pr_id: int, comment_id: int, username: Optional[str] = None):
    """
    Get comment details by PR ID and comment ID.
    
    Args:
        pr_id: PR number
        comment_id: Comment ID
        username: Optional username filter
    
    Returns:
        Comment details dictionary or error
    """
    try:
        base_dir = get_base_dir()
        db_path = getDBPath(base_dir)
        
        if not db_path.exists():
            return {"error": f"Database not found: {db_path}"}
        
        db_conn = sqlite3.connect(str(db_path))
        
        # Get comment details
        comment_details = get_comment_details(
            db_conn, 
            pr_id=pr_id, 
            comment_id=comment_id,
            username=username
        )
        
        db_conn.close()
        
        if comment_details:
            return {"success": True, "data": comment_details}
        else:
            return {"success": False, "error": f"Comment {comment_id} not found in PR {pr_id}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 3. Get PR Files

```python
@app.get("/api/pr/{pr_id}/files")
def get_files(pr_id: int, username: Optional[str] = None):
    """
    Get all files changed in a PR.
    
    Args:
        pr_id: PR number
        username: Optional username filter
    
    Returns:
        List of file details or error
    """
    try:
        base_dir = get_base_dir()
        db_path = getDBPath(base_dir)
        
        if not db_path.exists():
            return {"error": f"Database not found: {db_path}"}
        
        db_conn = sqlite3.connect(str(db_path))
        
        # Get PR files
        files_list = get_pr_files(
            db_conn, 
            pr_id=pr_id,
            username=username
        )
        
        db_conn.close()
        
        if files_list:
            # Calculate summary stats
            total_additions = sum(f.get('additions', 0) for f in files_list)
            total_deletions = sum(f.get('deletions', 0) for f in files_list)
            total_changes = sum(f.get('changes', 0) for f in files_list)
            
            return {
                "success": True, 
                "data": {
                    "files": files_list,
                    "summary": {
                        "total_files": len(files_list),
                        "total_additions": total_additions,
                        "total_deletions": total_deletions,
                        "total_changes": total_changes
                    }
                }
            }
        else:
            return {"success": False, "error": f"Files not found for PR {pr_id}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Example Usage

Once the endpoint is added, you can call it from the Electron renderer:

```typescript
// From Electron renderer
const response = await fetch('http://localhost:3000/api/pr/9258');
const data = await response.json();

if (data.success) {
  console.log('PR Title:', data.data.pr_title);
  console.log('PR Author:', data.data.pr_author);
  console.log('PR URL:', data.data.pr_html_url);
} else {
  console.error('Error:', data.error);
}
```

## Testing the Endpoints

1. **Start the server** (with base_dir argument):
   ```bash
   cd apps/falcon-iq-electron-app/src/python
   python server.py 3000 ~/Library/Application\ Support/Falcon\ IQ true
   ```

2. **Test PR endpoint**:
   ```bash
   # Get PR details
   curl http://localhost:3000/api/pr/9258
   
   # With username filter
   curl http://localhost:3000/api/pr/9258?username=npurwar
   ```

3. **Test comment endpoint**:
   ```bash
   # Get comment details
   curl http://localhost:3000/api/pr/9258/comment/123456
   
   # With username filter
   curl http://localhost:3000/api/pr/9258/comment/123456?username=npurwar
   ```

4. **Test files endpoint**:
   ```bash
   # Get all files changed in PR
   curl http://localhost:3000/api/pr/16347/files
   
   # With username filter
   curl http://localhost:3000/api/pr/16347/files?username=npurwar
   ```

## Key Points

✅ **No manual base_dir setup needed** - Environment variable is already set by server.py  
✅ **Works with both dev and prod databases** - Controlled by `IS_DEV` environment variable  
✅ **Thread-safe** - Uses database connections per request  
✅ **Error handling** - Returns proper error responses if PR not found or database issues  

## Advanced: Get PR with Comments

You could extend this to also fetch comments:

```python
@app.get("/api/pr/{pr_id}/full")
def get_pr_full(pr_id: int, username: Optional[str] = None):
    """
    Get PR details with all comments.
    """
    try:
        base_dir = get_base_dir()
        db_path = getDBPath(base_dir)
        db_conn = sqlite3.connect(str(db_path))
        
        # Get PR details
        pr_details = get_pr_details(db_conn, pr_id=pr_id, username=username)
        
        if not pr_details:
            db_conn.close()
            return {"success": False, "error": "PR not found"}
        
        # Get comments from pr_comment_details table
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT username, comment_type, created_at, is_reviewer, 
                   primary_category, severity, rationale
            FROM pr_comment_details
            WHERE pr_number = ?
            ORDER BY created_at
        """, (pr_id,))
        
        comments = []
        for row in cursor.fetchall():
            comments.append({
                'username': row[0],
                'comment_type': row[1],
                'created_at': row[2],
                'is_reviewer': bool(row[3]),
                'primary_category': row[4],
                'severity': row[5],
                'rationale': row[6]
            })
        
        db_conn.close()
        
        return {
            "success": True,
            "data": {
                "pr": pr_details,
                "comments": comments,
                "comment_count": len(comments)
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Summary

The integration is seamless because:
1. `server.py` sets `FALCON_BASE_DIR` environment variable at startup
2. `prDataReader.py` uses `common.py` which reads this environment variable
3. No additional configuration or setup needed in endpoint code
4. Works consistently across all environments (dev/prod)
