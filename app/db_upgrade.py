"""Small, safe upgrade for databases created by an earlier version of the app."""
from datetime import datetime
from sqlalchemy import inspect, text
from app import db


def upgrade_chat_tables():
    """Adds chat_message.session_id if missing and moves old loose messages into a chat."""
    if 'chat_message' not in inspect(db.engine).get_table_names():
        return

    columns = [c['name'] for c in inspect(db.engine).get_columns('chat_message')]
    if 'session_id' not in columns:
        db.session.execute(text('ALTER TABLE chat_message ADD COLUMN session_id INTEGER'))
        db.session.commit()

    groups = db.session.execute(text(
        'SELECT DISTINCT user_id, subject_id FROM chat_message WHERE session_id IS NULL')).fetchall()
    for user_id, subject_id in groups:
        first = db.session.execute(text(
            "SELECT text FROM chat_message WHERE session_id IS NULL AND user_id = :u AND subject_id = :s "
            "AND role = 'user' ORDER BY id LIMIT 1"), {'u': user_id, 's': subject_id}).fetchone()
        title = (first[0][:45] if first else 'Earlier chat') or 'Earlier chat'
        now = datetime.utcnow()
        result = db.session.execute(text(
            'INSERT INTO chat_session (user_id, subject_id, title, created_at, updated_at) '
            'VALUES (:u, :s, :t, :n, :n)'), {'u': user_id, 's': subject_id, 't': title, 'n': now})
        db.session.execute(text(
            'UPDATE chat_message SET session_id = :sid WHERE session_id IS NULL AND user_id = :u AND subject_id = :s'),
            {'sid': result.lastrowid, 'u': user_id, 's': subject_id})
    db.session.commit()


def upgrade_user_premium():
    """Adds user.premium_until if the database was created before the Premium feature."""
    if 'user' not in inspect(db.engine).get_table_names():
        return
    columns = [c['name'] for c in inspect(db.engine).get_columns('user')]
    if 'premium_until' not in columns:
        db.session.execute(text('ALTER TABLE "user" ADD COLUMN premium_until DATETIME'))
        db.session.commit()
