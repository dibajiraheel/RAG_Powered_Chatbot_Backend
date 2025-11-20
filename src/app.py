from fastapi import FastAPI
from routes.user_routes import user_router
from routes.document_routes import document_routes
from routes.graphs_routes import graphs_routes
from starlette.middleware.cors import CORSMiddleware


from contextlib import asynccontextmanager

import psycopg_pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


import files_to_load.config_to_load as config_to_load_at_initialization

from langgraph.checkpoint.postgres import PostgresSaver
from db_connection.db_base import Base

from config import config
from graph.main_graph import main_graph

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from langchain_openai import ChatOpenAI

neon_connection_string = config.neon_postgresql_db_url
min_db_connection = int(config.min_db_connection)
max_db_connection = int(config.max_db_connection)

# Database Global Resources
DB_POOL: psycopg_pool.ConnectionPool | None = None



@asynccontextmanager
async def lifespan(app: FastAPI):
    global DB_POOL

    ### 🚀 STARTUP Phase: Initialize ALL Resources
    try:
        # A. Initialize SQLAlchemy Engine and Session maker

        config_to_load_at_initialization.SQLALCHEMY_ENGINE = create_engine(
            neon_connection_string,
            pool_size=3,
            max_overflow=2,
            pool_recycle=300,        
            pool_pre_ping=True,      
            pool_timeout=30,
        )

        config_to_load_at_initialization.SessionLocal = sessionmaker(bind=config_to_load_at_initialization.SQLALCHEMY_ENGINE, autocommit=False, autoflush=False)
        
        # B. Create SQLAlchemy tables (if they don't exist)
        Base.metadata.create_all(config_to_load_at_initialization.SQLALCHEMY_ENGINE)
        print("✅ SQLAlchemy tables checked/created.")

        # C. Initialize LangGraph DB_POOL (Local, Thread-Safe Pool)
        DB_POOL = psycopg_pool.ConnectionPool(
            conninfo=neon_connection_string, 
            min_size=min_db_connection,     
            max_size=max_db_connection,
            check=psycopg_pool.ConnectionPool.check_connection,
            max_idle=300,
            kwargs={
                    "autocommit": True,        
                    "prepare_threshold": 0,    
                    }
        )
        print("✅ LangGraph DB_POOL (psycopg_pool) initialized.")


        # D. Setup LangGraph Checkpointer
        config_to_load_at_initialization.POSTGRES_CHECKPOINTER = PostgresSaver(DB_POOL) 
        config_to_load_at_initialization.POSTGRES_CHECKPOINTER.setup()
        print("✅ LangGraph checkpointer setup complete.")

        # E. Compile the graph
        config_to_load_at_initialization.COMPILED_MAIN_GRAPH = main_graph.compile(checkpointer=config_to_load_at_initialization.POSTGRES_CHECKPOINTER)
        print("✅ LangGraph compiled and ready.")

        # F. Initialize Embedding Models
        config_to_load_at_initialization.SMALL_EMBEDDING_MODEL = OpenAIEmbeddings(model = config.openai_embedding_model_name)
        config_to_load_at_initialization.LARGE_EMBEDDING_MODEL = OpenAIEmbeddings(model = config.openai_embedding_model_name)
        print("✅ Embedding Models initialized.")

        # G. Initialize Vector Stores (PGVector)
    
        config_to_load_at_initialization.SMALL_DOCS_VECTOR_STORE = PGVector(
            embeddings=config_to_load_at_initialization.SMALL_EMBEDDING_MODEL,
            collection_name=config.small_vector_store_collection_name,
            connection=config_to_load_at_initialization.SQLALCHEMY_ENGINE,
            use_jsonb=True
        )
        config_to_load_at_initialization.LARGE_DOCS_VECTOR_STORE = PGVector(
            embeddings=config_to_load_at_initialization.LARGE_EMBEDDING_MODEL,
            collection_name=config.large_vector_store_colletion_name,
            connection=config_to_load_at_initialization.SQLALCHEMY_ENGINE,
            use_jsonb=True
        )
        print("✅ PGVector Stores initialized.")

        # H. Initialize LLM Models
        config_to_load_at_initialization.LLM_OPENAI = ChatOpenAI(model = config.openai_chat_model_name)
        print("✅ OpenAI LLM Model initialized.")

    except Exception as e:
        print(f"FATAL ERROR during startup: Could not initialize resources. {e}")
        raise RuntimeError("Failed to initialize database or graph.") from e
        
    yield # <--- Application starts serving requests here

    ### 🛑 SHUTDOWN Phase: Close the Pools/Engines
    print("Application shutdown initiated.")
    if DB_POOL:
        DB_POOL.close() # Close the LangGraph pool
        print("✅ DB_POOL closed gracefully.")
    if config_to_load_at_initialization.SQLALCHEMY_ENGINE:
        config_to_load_at_initialization.SQLALCHEMY_ENGINE.dispose() # Dispose of the SQLAlchemy engine
        print("✅ SQLAlchemy Engine disposed gracefully.")





origins = [config.frontend_url]

app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware,
                   allow_origins = origins,
                   allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], 
                   allow_headers = ["Content-Type", "Authorization", "Accept"],
                   max_age=3600
                   )

app.include_router(user_router, prefix = '/user', tags = ['user routes'])
app.include_router(document_routes, prefix='/document', tags=['document routes'])
app.include_router(graphs_routes, prefix='/graphs', tags = ['graphs', 'routes'])

@app.get('/health')
async def health():
    # 1. Get SQLAlchemy Pool Status
    sql_pool = config_to_load_at_initialization.SQLALCHEMY_ENGINE.pool
    
    # 2. Get psycopg_pool Status (Requires DB_POOL to be defined globally)
    global DB_POOL # Ensure you access the global variable
    
    if DB_POOL is None:
        psycopg_status = {"error": "DB_POOL not initialized"}
    else:
        psycopg_status = DB_POOL._stats 

    return {
        "status": "healthy",
        
        "sqlalchemy_pool": {
            "pool_size": sql_pool.size(),
            "checked_out": sql_pool.checkedout(),
            "overflow": sql_pool.overflow(),
        },
        
        "psycopg_pool": psycopg_status, # Include the new metrics
    }



















