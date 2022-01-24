import boto3
import logging
from contextlib import closing

logger = logging.getLogger()
logger.setLevel(logging.INFO)

comprehend = boto3.client('comprehend')
polly = boto3.client('polly')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

languages = {'pl':'Maja','en':'Matthew','de':'Vicki','fr':'Celine','ja':'Mizuki'}


def lambda_handler(event, context):
    logger.info('Creating Audio file based on event: %s', event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    file = event['Records'][0]['s3']['object']['key']

    # Read txt
    obj = s3.get_object(Bucket=bucket, Key=file)
    content = obj["Body"].read().decode("utf-8").replace('\n',' ')
    logger.info('Content: %s', content);
    
    # Detect language
    response = comprehend.detect_dominant_language(
        Text=content
    )
    language = response['Languages'][0]['LanguageCode']
    voice =  languages[language]

    logger.info('Language: %s', language);
    logger.info('Voice: %s', voice);

    # Using Amazon Polly service to convert text to speech
    response = polly.synthesize_speech(
        OutputFormat='mp3',
        Text=content,
        TextType='text',
        VoiceId=voice
    )

    # Save audio in local directory
    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            with open("/tmp/audio.mp3", "wb") as audioFile:
                audioFile.write(stream.read())

    # Save audio file in S3
    newName =  file.split('/')[-1][:-4] + ".mp3"
    s3.upload_file("/tmp/audio.mp3", bucket, "page/"+newName)

    #Adding information about new audio file to DynamoDB table
    table = dynamodb.Table("Interactions")
    table.put_item(
        Item={
            'name' : newName,
            'text' : content,
            'language' : language,
            'voice' : voice
        }
    )

    return "OK"
