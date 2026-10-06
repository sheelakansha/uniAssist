"""Create an empty, durable Chroma collection. It never inserts demo data."""
import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import chromadb

host=os.getenv('CHROMA_HOST','localhost')
port=int(os.getenv('CHROMA_PORT','8001'))
client=chromadb.HttpClient(host=host,port=port)
print('Chroma heartbeat:',client.heartbeat())
collection=client.get_or_create_collection('nsut_knowledge',metadata={'hnsw:space':'cosine'})
print(f"Collection ready: {collection.name}; documents: {collection.count()}")
