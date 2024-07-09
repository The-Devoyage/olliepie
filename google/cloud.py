from google.cloud import storage
import os

# Upload to GCS
def upload_to_gcs(source_file_path, destination_blob_name):
    bucket_name = os.getenv('BUCKET_NAME')
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)
    print('File {} uploaded to {}.'.format(source_file_path, destination_blob_name))
