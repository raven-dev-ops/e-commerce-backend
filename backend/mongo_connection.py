# backend/mongo_connection.py

import logging
import mongoengine
import os

logger = logging.getLogger(__name__)


def connect_mongodb():
    logger.info("Attempting to connect to MongoDB...")
    mongodb_uri = os.environ.get("MONGODB_URI")

    if mongodb_uri:
        try:
            mongoengine.connect(host=mongodb_uri)
            logger.info("MongoDB connection established successfully.")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}", exc_info=True)
            # Re-raise the exception to allow it to propagate and be visible in Heroku logs
            raise
    else:
        logger.error("MONGODB_URI environment variable not set.")
        # Raise an error as this is a critical configuration issue
        raise EnvironmentError("MONGODB_URI environment variable not set.")


if __name__ == "__main__":
    # This block is for testing the connection
    connect_mongodb()
    logger.info("MongoDB connection established successfully.")
    # You can add a small test query here if you have a model defined
    # from your_app.models import YourModel
    # logger.info(YourModel.objects.first())
