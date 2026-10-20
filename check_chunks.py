# Project folder-er vitore rekhe chalao: venv_new\Scripts\python.exe check_chunks.py
from app import create_app
from app.models import Document
from app.rag import collection

app = create_app()
with app.app_context():
    print("Total chunks in ChromaDB:", collection.count())
    docs = Document.query.all()
    if not docs:
        print("Database-e kono document nai.")
    for d in docs:
        got = collection.get(where={"document_id": d.id})
        print(f"Document {d.id} | subject {d.subject_id} | {d.filename} -> {len(got['ids'])} chunks")