from instagrapi import Client
import inspect

methods = inspect.getmembers(Client, predicate=inspect.isfunction)
schedule_methods = [m[0] for m in methods if 'schedule' in m[0] or 'publish' in m[0]]
print("Methods related to scheduling/publishing:", schedule_methods)

# Check signature of photo_upload
sig = inspect.signature(Client.photo_upload)
print("\nSignature of photo_upload:", sig)
