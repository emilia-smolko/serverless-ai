import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    logger.info('Starting Analyzing Image for event: %s', event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    file = event['Records'][0]['s3']['object']['key']

    description = "";

    # Invoke Rekognition service
    celebrities = rekognition.recognize_celebrities(Image={ 'S3Object': { 'Bucket': bucket, 'Name': file } })["CelebrityFaces"]

    if len(celebrities) == 0:
        description = "I can't see anybody famous on the picture!"

    if len(celebrities) > 0:
        names = []
        for celebrity in celebrities:
            names.append(celebrity["Name"])

        description = "I can see " + ', '.join(names) + " on the picture!";

    logger.info('Description: %s', description);

    #Saving description to S3
    txtName = 'tmp/' + file[:-4] + ".txt"
    s3.put_object(Body=description, Bucket=bucket, Key=txtName)

    return {
        'statusCode': 200,
        'body': json.dumps(description)
    }