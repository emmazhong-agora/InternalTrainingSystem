from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(
    url="http://localhost:6333",  # REST API endpoint
    prefer_grpc=False             # Force HTTP mode
)
# client = QdrantClient(
#     "http://localhost:6333",
#     timeout=10,
#     prefer_grpc=False,
#     http_client_kwargs={"proxies": None}
# )


client.recreate_collection(
    collection_name="test_vectors2",
    vectors_config=VectorParams(size=4, distance=Distance.COSINE)
)

print(client.get_collections())
