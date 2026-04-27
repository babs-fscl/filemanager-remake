import sqlite3
import uuid

def migrate():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check if 'uuid' column exists in file_document
    cursor.execute("PRAGMA table_info(file_document)")
    doc_columns = [col[1] for col in cursor.fetchall()]
    if 'uuid' not in doc_columns:
        print("Adding uuid column to file_document...")
        cursor.execute("ALTER TABLE file_document ADD COLUMN uuid CHAR(32)")
    
    # Check if 'uuid' column exists in file_project
    cursor.execute("PRAGMA table_info(file_project)")
    proj_columns = [col[1] for col in cursor.fetchall()]
    if 'uuid' not in proj_columns:
        print("Adding uuid column to file_project...")
        cursor.execute("ALTER TABLE file_project ADD COLUMN uuid CHAR(32)")
    
    # Populate empty UUIDs
    cursor.execute("SELECT id FROM file_document WHERE uuid IS NULL")
    docs = cursor.fetchall()
    for doc_id, in docs:
        new_uuid = uuid.uuid4().hex
        cursor.execute("UPDATE file_document SET uuid = ? WHERE id = ?", (new_uuid, doc_id))
    
    cursor.execute("SELECT id FROM file_project WHERE uuid IS NULL")
    projs = cursor.fetchall()
    for proj_id, in projs:
        new_uuid = uuid.uuid4().hex
        cursor.execute("UPDATE file_project SET uuid = ? WHERE id = ?", (new_uuid, proj_id))
    
    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
