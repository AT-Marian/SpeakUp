from pymongo import MongoClient

# This is the string we verified was working earlier
uri = "mongodb+srv://AT-Marian:Tm200114@cluster0.bibltvc.mongodb.net/speakup?retryWrites=true&w=majority"

try:
    print("Attempting to connect...")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ DATABASE CONNECTION SUCCESSFUL")
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")