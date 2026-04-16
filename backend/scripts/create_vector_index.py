"""
Run once after creating your MongoDB Atlas cluster to set up the vector search index.

Usage:
    cd backend
    python scripts/create_vector_index.py
"""
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import get_settings

settings = get_settings()

INDEX_DEFINITION = {
    "name": settings.mongodb_vector_index_name,
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {
                "type": "vector",
                "path": "embeddings.combined",
                "numDimensions": settings.embedding_dimension,
                "similarity": "cosine",
            },
            {
                "type": "filter",
                "path": "source",
            },
            {
                "type": "filter",
                "path": "summary.content_type",
            },
            {
                "type": "filter",
                "path": "summary.language",
            },
        ]
    },
}


async def create_index():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    collection = db[settings.mongodb_collection_content]

    # Check if index already exists
    existing = await collection.list_search_indexes().to_list(None)
    existing_names = [idx.get("name") for idx in existing]

    if settings.mongodb_vector_index_name in existing_names:
        print(f"Index '{settings.mongodb_vector_index_name}' already exists.")
    else:
        await collection.create_search_index(INDEX_DEFINITION)
        print(f"Vector search index '{settings.mongodb_vector_index_name}' created.")
        print("Note: Atlas takes 1-5 minutes to build the index. Check Atlas UI for status.")

    client.close()


if __name__ == "__main__":
    asyncio.run(create_index())
