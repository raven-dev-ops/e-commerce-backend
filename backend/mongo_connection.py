#mongo_connection.py

import mongoengine
import os

def connect_mongodb():
    # Get the MongoDB connection string from the environment variable 
    mongodb_uri = os.environ.get('MONGODB_URI')

    if mongodb_uri:
        mongoengine.connect(host=mongodb_uri)
    else:
        # Handle the case where the environment variable is not set 
        print("Error: MONGODB_URI environment variable not set.") 
        # You might want to raise an exception or handle this case appropriately 
if __name__ == '__main__':
    # This block is for testing the connection
    connect_mongodb()
    print("MongoDB connection established successfully.")
    # You can add a small test query here if you have a model defined
    # from your_app.models import YourModel
    # print(YourModel.objects.first())