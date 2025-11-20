from sqlalchemy.orm import Session
from typing import Iterator

# 1. Define the globals here (uninitialized)
SQLALCHEMY_ENGINE = None
SessionLocal = None
COMPILED_MAIN_GRAPH = None # Global for your LangGraph instanc


SMALL_EMBEDDING_MODEL = None
LARGE_EMBEDDING_MODEL = None
SMALL_DOCS_VECTOR_STORE = None
LARGE_DOCS_VECTOR_STORE = None

LLM_OPENAI = None

POSTGRES_CHECKPOINTER = None











def get_db_session() -> Iterator[Session]:
    # This dependency uses the globals defined above.
    if SessionLocal is None:
        raise Exception("Database SessionLocal not initialized. Check application lifespan.")
        
    db = SessionLocal()
    print('NEW CONNECTION OF DB GENERATED') 
    try:
        yield db
    finally:
        db.close()
        print('DB CONNECTION CLOSED')

