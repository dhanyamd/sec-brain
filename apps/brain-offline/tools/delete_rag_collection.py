from pymongo import MongoClient
from pymongo.database import Database

from src.second_brain_offline.config import settings


def delete_rag_collection(
    mongo_uri: str = settings.MONGODB_URI, db_name: str = settings.MONGODB_DATABASE_NAME
) -> None:
    """
    Deletes the 'rag' collection from the specified MongoDB database.

    Args:
        mongo_uri: The MongoDB connection URI string. Defaults to local MongoDB instance.
        db_name: The name of the database containing the 'rag' collection.
                Defaults to 'second_brain'.

    Raises:
        pymongo.errors.ConnectionError: If connection to MongoDB fails.
        pymongo.errors.OperationFailure: If deletion operation fails.
    """

    # Create MongoDB client
    client = MongoClient(mongo_uri)

    # Get database
    db: Database = client[db_name]

    # Delete 'rag' collection if it exists
    if "rag" in db.list_collection_names():
        db.drop_collection("rag")
        print("Successfully deleted 'rag' collection.")
    else:
        print("'rag' collection does not exist.")

    # Close the connection
    client.close()


if __name__ == "__main__":
    delete_rag_collection()