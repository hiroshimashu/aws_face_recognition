from __future__ import print_function

import boto3
from decimal import Decimal
import json
import urllib

print('Loading function')

dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
collectionId = "face_reference"
threshold = 70
maxFaces=2


# --------------- Helper Functions ------------------

def index_faces(bucket, key):
    # --- Step1. search for collection: --- 
    precision = detect_face(bucket, key)
    print(precision)
    # --- Step2. Add to the reference collection: ---
    if precision < 90: 
        response = rekognition.index_faces(
            Image={"S3Object":
                {"Bucket": bucket,
                 "Name": key}},
                 CollectionId="face_reference")
        return response
    return False
    
def update_index(tableName,faceId):
    response = dynamodb.put_item(
        TableName=tableName,
        Item={
            'RekognitionId': {'S': faceId},
            }
        )

def detect_face(bucket,key):
    accuracy = None
    result = rekognition.search_faces_by_image(CollectionId=collectionId,
                                Image={'S3Object':
                                    {'Bucket':bucket,
                                    'Name':key}},
                                FaceMatchThreshold=threshold,
                                MaxFaces=maxFaces)
    print(result)
    faceMatches = result['FaceMatches']
    print ('Matching faces')
    for match in faceMatches:
            print ('FaceId:' + match['Face']['FaceId'])
            accuracy = match['Similarity']
    return accuracy
    
    
# --------------- Main handler ------------------

def lambda_handler(event, context):

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(
        event['Records'][0]['s3']['object']['key'].encode('utf8'))

    try:

        # Calls Amazon Rekognition IndexFaces API to detect faces in S3 object 
        # to index faces into specified collection
        
        response = index_faces(bucket, key)
        
        # Commit faceId and full name object metadata to DynamoDB
        if response == False:
            print("image has matched")
        elif response['ResponseMetadata']['HTTPStatusCode'] == 200:
            faceId = response['FaceRecords'][0]['Face']['FaceId']
            update_index('face-reference',faceId)

        # Print response to console
        print(response)

        return response
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket))
        raise e