from django.test import TestCase
from mongoengine import connect, disconnect
import mongomock


class MongoTestCase(TestCase):
    """
    Base TestCase for tests that use MongoEngine with mongomock.

    Ensures a clean in-memory MongoDB connection is available for each
    test class and torn down afterwards.
    """

    mongo_db_name = "mongoenginetest"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disconnect()
        connect(
            cls.mongo_db_name,
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
        )

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

