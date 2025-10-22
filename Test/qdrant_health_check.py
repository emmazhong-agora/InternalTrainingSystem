from qdrant_client import QdrantClient


def main() -> None:
    client = QdrantClient(
        url="http://localhost:6334",
        prefer_grpc=False,
        timeout=5,
    )

    health = client.http.service_api.healthz()
    print("Health status:", health.status)

    collections = client.get_collections()
    print("Collections:", [collection.name for collection in collections.collections])


if __name__ == "__main__":
    main()
