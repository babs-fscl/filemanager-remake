import sqlite3
import os

def check():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    log = []
    
    # Check users
    cursor.execute("SELECT email, role, organization_id, is_active FROM authentication_customuser")
    users = cursor.fetchall()
    log.append(f"Users found: {len(users)}")
    for u in users:
        log.append(f"User: {u[0]}, Role: {u[1]}, OrgID: {u[2]}, Active: {u[3]}")
        
    conn.close()
    
    with open('user_diag.txt', 'w') as f:
        f.write("\n".join(log))

if __name__ == "__main__":
    check()
