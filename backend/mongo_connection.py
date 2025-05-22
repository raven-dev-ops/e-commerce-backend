import mongoengine

def connect_mongodb():
    mongoengine.connect(
        db='website',
        host='mongodb+srv://gptfleet:GyUeIj6ohuDZhnVi@website.ora74qp.mongodb.net/',
        authSource='admin',
        retryWrites=True,
        w='majority'
    )

if __name__ == '__main__':
    # This block is for testing the connection
    connect_mongodb()
    print("MongoDB connection established successfully.")
    # You can add a small test query here if you have a model defined
    # from your_app.models import YourModel
    # print(YourModel.objects.first())