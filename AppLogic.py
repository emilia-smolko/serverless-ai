import json
import boto3
import logging
import base64
import urllib.request
import uuid
import time
from boto3.dynamodb.conditions import Key, Attr


logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambdaClient = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sns = boto3.client('sns')
connect = boto3.client('connect')
myBucketName = "data-for-my-app"

def lambda_handler(event, context):
    logger.info('Event: %s', event);
    payload = json.loads(json.dumps(event['body']))
    payload = json.loads(base64.b64decode(payload).decode())

    text = payload["text"]
    image = payload["image"]
    phone = '+48' + payload["phone"]
    type = payload["type"]

    logger.info('Params');
    logger.info('Text: %s', text);
    logger.info('Image: %s', image);
    logger.info('Phone Number: %s', phone);
    logger.info('Type: %s', type);


    file_id = str(uuid.uuid4());

    if image:
        downloadImageToS3(file_id, image)
    else:
        createTextFile(file_id, text);

    logger.info('file_id: %s', file_id);
    #Wait until result will be in DynamoDB
    table = dynamodb.Table("Interactions")
    file_id = file_id+'.mp3'
    while True:
        time.sleep(3)
        items = table.query(KeyConditionExpression=Key('name').eq(file_id))
        if len(items['Items']) > 0:
            url = 'xxx'+file_id
            language = items['Items'][0]['language']
            text = items['Items'][0]['text']
            break;
        else:
            time.sleep(0.5)


    if type == 2:
        logger.info('Sending SMS: %s', url);
        sns.publish( PhoneNumber=phone, Message = url, MessageAttributes={'AWS.SNS.SMS.SenderID': {'DataType': 'String', 'StringValue': "CHMURA"}, 'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': 'Promotional'}} );

    if type == 3:
        callUser(language, text, phone)


    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
            },
        'body': file_id
    };

def createTextFile(file_id, text):
    file = file_id + ".txt";
    f = open('/tmp/' + file, "w")
    f.write(text)
    f.close()
    s3.upload_file('/tmp/' + file, myBucketName, file)

def downloadImageToS3(file_id, image):
    file = file_id + ".jpg";
    urllib.request.urlretrieve(image, '/tmp/' + file)
    s3.upload_file('/tmp/' + file, myBucketName, file)


def callUser(language, text, phone):


    logger.info('Calling!');
    logger.info('Phone Number: %s ...', phone[0:9]);
    logger.info('Text: %s', text);
    logger.info('Language: %s', language);

    connect.start_outbound_voice_contact(
        DestinationPhoneNumber=phone,
        ContactFlowId='xxx',
        InstanceId='xxx',
        SourcePhoneNumber='xxx',
        Attributes={
            'text': text,
            'language':language
        }
    )