from typing import Generic, Type, TypeVar

from bson import ObjectId
from pydantic import BaseModel
from pymongo import MongoClient, errors

from second_brain_offline.config import settings

T = TypeVar("T", bound=BaseModel)


class MongoDBService(Generic[T]):
    """Service class for MongoDB operations, supporting ingestion, querying, and validation.

    This class provides methods to interact with MongoDB collections, including document
    ingestion, querying, and validation operations.

    Args:
        model: The Pydantic model class to use for document serialization.
        collection_name: Name of the MongoDB collection to use.
        database_name: Name of the MongoDB database to use.
        mongodb_uri: URI for connecting to MongoDB instance.

    Attributes:
        model: The Pydantic model class used for document serialization.
        collection_name: Name of the MongoDB collection.
        database_name: Name of the MongoDB database.
        mongodb_uri: MongoDB connection URI.
        client: MongoDB client instance for database connections.
        database: Reference to the target MongoDB database.
        collection: Reference to the target MongoDB collection.
    """

    def __init__(
        self,
        model: Type[T],
        collection_name: str,
        database_name: str = settings.MONGODB_DATABASE_NAME,
        mongodb_uri: str = settings.MONGODB_URI,
    ) -> None:
        """Initialize a connection to the MongoDB collection.

        Args:
            collection_name: Name of the MongoDB collection to use.
            model_class: The Pydantic model class to use for document serialization.
            database_name: Name of the MongoDB database to use.
                Defaults to value from settings.
            mongodb_uri: URI for connecting to MongoDB instance.
                Defaults to value from settings.

        Raises:
            Exception: If connection to MongoDB fails.
        """

        self.model = model
        self.collection_name = collection_name
        self.database_name = database_name
        self.mongodb_uri = mongodb_uri

        try:
            self.client = MongoClient(mongodb_uri, appname="second_brain_course")
            self.client.admin.command("ping")
        except Exception as e:
            print(f"Failed to initialize MongoDBService: {e}")
            raise

        self.database = self.client[database_name]
        self.collection = self.database[collection_name]
        print(
            f"Connected to MongoDB instance:\n URI: {mongodb_uri}\n Database: {database_name}\n Collection: {collection_name}"
        )

    def __enter__(self) -> "MongoDBService":
        """Enable context manager support.

        Returns:
            MongoDBService: The current instance.
        """

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close MongoDB connection when exiting context.

        Args:
            exc_type: Type of exception that occurred, if any.
            exc_val: Exception instance that occurred, if any.
            exc_tb: Traceback of exception that occurred, if any.
        """

        self.close()

    def clear_collection(self) -> None:
        """Remove all documents from the collection.

        This method deletes all documents in the collection to avoid duplicates
        during reingestion.

        Raises:
            errors.PyMongoError: If the deletion operation fails.
        """

        try:
            result = self.collection.delete_many({})
            print(
                f"Cleared collection. Deleted {result.deleted_count} documents."
            )
        except errors.PyMongoError as e:
            print(f"Error clearing the collection: {e}")
            raise

    def ingest_documents(self, documents: list[T]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            documents: List of Pydantic model instances to insert.

        Raises:
            ValueError: If documents is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """

        try:
            if not documents or not all(
                isinstance(doc, BaseModel) for doc in documents
            ):
                raise ValueError("Documents must be a list of Pycantic models.")

            dict_documents = [doc.model_dump() for doc in documents]

            # Remove '_id' fields to avoid duplicate key errors
            for doc in dict_documents:
                doc.pop("_id", None)

            self.collection.insert_many(dict_documents)
            print(f"Inserted {len(documents)} documents into MongoDB.")
        except errors.PyMongoError as e:
            print(f"Error inserting documents: {e}")
            raise

    def fetch_documents(self, limit: int, query: dict) -> list[T]:
        """Retrieve documents from the MongoDB collection based on a query.

        Args:
            limit: Maximum number of documents to retrieve.
            query: MongoDB query filter to apply.

        Returns:
            List of Pydantic model instances matching the query criteria.

        Raises:
            Exception: If the query operation fails.
        """
        try:
            documents = list(self.collection.find(query).limit(limit))
            print(f"Fetched {len(documents)} documents with query: {query}")
            return self.__parse_documents(documents)
        except Exception as e:
            print(f"Error fetching documents: {e}")
            raise

    def __parse_documents(self, documents: list[dict]) -> list[T]:
        """Convert MongoDB documents to Pydantic model instances.

        Converts MongoDB ObjectId fields to strings and transforms the document structure
        to match the Pydantic model schema.

        Args:
            documents: List of MongoDB documents to parse.

        Returns:
            List of validated Pydantic model instances.
        """
        parsed_documents = []
        for doc in documents:
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    doc[key] = str(value)

            _id = doc.pop("_id", None)
            doc["id"] = _id

            parsed_doc = self.model.model_validate(doc)
            parsed_documents.append(parsed_doc)

        return parsed_documents

    def get_collection_count(self) -> int:
        """Count the total number of documents in the collection.

        Returns:
            Total number of documents in the collection.

        Raises:
            errors.PyMongoError: If the count operation fails.
        """

        try:
            return self.collection.count_documents({})
        except errors.PyMongoError as e:
            print(f"Error counting documents in MongoDB: {e}")
            raise

    def close(self) -> None:
        """Close the MongoDB connection.

        This method should be called when the service is no longer needed
        to properly release resources, unless using the context manager.
        """

        self.client.close()
        print("Closed MongoDB connection.")