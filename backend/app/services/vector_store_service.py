import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from openai import OpenAI
import os
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing video transcript embeddings using ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB client and OpenAI client."""
        # Initialize ChromaDB with persistent storage
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        logger.info("VectorStoreService initialized with ChromaDB")

    def _get_or_create_collection(self, video_id: int):
        """
        Get or create a ChromaDB collection for a specific video.

        Args:
            video_id: The ID of the video

        Returns:
            ChromaDB collection object
        """
        collection_name = f"video_{video_id}_transcripts"

        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"video_id": video_id}
            )
            logger.info(f"Using collection: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI's embedding model.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Filter out empty strings and clean text
            cleaned_texts = [text.strip() for text in texts if text and text.strip()]

            if not cleaned_texts:
                logger.error("No valid text to embed after filtering")
                raise ValueError("No valid text content to embed")

            logger.info(f"Generating embeddings for {len(cleaned_texts)} texts")
            logger.debug(f"First text sample: {cleaned_texts[0][:100]}...")

            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",  # Using latest efficient model
                input=cleaned_texts
            )
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def add_transcript_chunks(
        self,
        video_id: int,
        chunks: List[Dict],
        clear_existing: bool = False
    ) -> bool:
        """
        Add transcript chunks to the vector store.

        Args:
            video_id: The ID of the video
            chunks: List of transcript chunks with 'text', 'start_time', 'end_time', 'index'
            clear_existing: If True, clear existing embeddings before adding new ones

        Returns:
            True if successful
        """
        try:
            collection = self._get_or_create_collection(video_id)

            # Clear existing data if requested
            if clear_existing:
                try:
                    self.chroma_client.delete_collection(f"video_{video_id}_transcripts")
                    collection = self._get_or_create_collection(video_id)
                    logger.info(f"Cleared existing embeddings for video {video_id}")
                except Exception as e:
                    logger.warning(f"Could not clear collection: {e}")

            # Prepare data for ChromaDB
            texts = [chunk['text'] for chunk in chunks]
            ids = [f"chunk_{video_id}_{chunk['index']}" for chunk in chunks]
            metadatas = [
                {
                    'video_id': video_id,
                    'start_time': chunk['start_time'],
                    'end_time': chunk['end_time'],
                    'index': chunk['index'],
                    'duration': chunk['end_time'] - chunk['start_time']
                }
                for chunk in chunks
            ]

            # Generate embeddings
            embeddings = self._generate_embeddings(texts)

            # Add to ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Successfully added {len(chunks)} chunks for video {video_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding transcript chunks for video {video_id}: {e}")
            raise

    def search_similar_chunks(
        self,
        video_id: int,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search for transcript chunks similar to the query.

        Args:
            video_id: The ID of the video
            query: The search query
            n_results: Number of results to return

        Returns:
            List of matching chunks with text, metadata, and similarity scores
        """
        try:
            collection = self._get_or_create_collection(video_id)

            # Check if collection has any documents
            if collection.count() == 0:
                logger.warning(f"Collection for video {video_id} is empty")
                return []

            # Generate embedding for query
            query_embedding = self._generate_embeddings([query])[0]

            # Search in ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, collection.count())
            )

            # Format results
            chunks = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    chunk = {
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'id': results['ids'][0][i]
                    }
                    chunks.append(chunk)

            logger.info(f"Found {len(chunks)} relevant chunks for query in video {video_id}")
            return chunks

        except Exception as e:
            logger.error(f"Error searching chunks for video {video_id}: {e}")
            raise

    def delete_video_embeddings(self, video_id: int) -> bool:
        """
        Delete all embeddings for a specific video.

        Args:
            video_id: The ID of the video

        Returns:
            True if successful
        """
        try:
            collection_name = f"video_{video_id}_transcripts"
            self.chroma_client.delete_collection(collection_name)
            logger.info(f"Deleted embeddings for video {video_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting embeddings for video {video_id}: {e}")
            return False

    def get_all_chunks(self, video_id: int) -> List[Dict]:
        """
        Get all transcript chunks for a video from the vector store.

        Args:
            video_id: The ID of the video

        Returns:
            List of all chunks with text and metadata, ordered by index
        """
        try:
            collection = self._get_or_create_collection(video_id)

            # Check if collection has any documents
            count = collection.count()
            if count == 0:
                logger.warning(f"Collection for video {video_id} is empty")
                return []

            # Get all documents from the collection
            results = collection.get(
                include=['documents', 'metadatas']
            )

            # Format results
            chunks = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'])):
                    chunk = {
                        'text': results['documents'][i],
                        'metadata': results['metadatas'][i],
                        'id': results['ids'][i]
                    }
                    chunks.append(chunk)

            # Sort by index to maintain order
            chunks.sort(key=lambda x: x['metadata'].get('index', 0))

            logger.info(f"Retrieved {len(chunks)} chunks for video {video_id}")
            return chunks

        except Exception as e:
            logger.error(f"Error getting all chunks for video {video_id}: {e}")
            return []

    def get_collection_info(self, video_id: int) -> Dict:
        """
        Get information about a video's collection.

        Args:
            video_id: The ID of the video

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self._get_or_create_collection(video_id)
            count = collection.count()

            return {
                'video_id': video_id,
                'collection_name': f"video_{video_id}_transcripts",
                'chunk_count': count,
                'exists': count > 0
            }
        except Exception as e:
            logger.error(f"Error getting collection info for video {video_id}: {e}")
            return {
                'video_id': video_id,
                'error': str(e)
            }


# Singleton instance
vector_store_service = VectorStoreService()
