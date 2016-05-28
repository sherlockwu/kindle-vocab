import sqlite3, base64, tempfile, os, boto3, traceback, urllib2, json

def update_user(event, words):
    # insert words in dynamodb
    table = event['table']
    user = {'fbid': event['fbid'],
            'words': words,
            'practice': []}
    response = table.put_item(Item=user)
    return response

def practice(event):
    assert(len(event['cur_words']) <= 10)
    for w in event['cur_words']:
        assert(isinstance(w, basestring))
        assert(len(w) < 255)
    assert(event['guess'] in event['cur_words'])
    assert(event['actual'] in event['cur_words'])
    row = {'cur_words': event['cur_words'],
	   'guess':     event['guess'],
	   'actual':    event['actual']};
    
    table = event['table']
    result = table.update_item(
        Key={
            'fbid': event['fbid'],
        },
        UpdateExpression='SET practice = list_append(practice, :i)',
        ExpressionAttributeValues={
            ':i': [row],
        },
        ReturnValues='UPDATED_NEW'
    )
    return result

def fetch_words(event):
    table = event['table']
    response = table.get_item(Key={'fbid': event['fbid']})
    if not 'Item' in response:
        update_user(event, [])
    response = table.get_item(Key={'fbid': event['fbid']})
    return response['Item']['words']

def upload(event):
    fd, path = tempfile.mkstemp(suffix='.db')
    f = os.fdopen(fd, 'wb')
    f.write(base64.b64decode(event['db']))
    f.close()
    conn = sqlite3.connect(path)
    words = [row[0] for row in conn.execute('SELECT word FROM words')]
    return update_user(event, words);

def lambda_handler(event, context):
    fn = {
        'upload': upload,
        'fetch_words': fetch_words,
        'practice': practice,
    }[event['op']]

    # authenticate with FB
    if not 'fbid' in event:
        event['fbid'] = '0'
    if event['fbid'] != '0':
        url = 'https://graph.facebook.com/me?access_token='+event['fbid'];
        response = urllib2.urlopen(url)
        info = json.loads(response.read())
        event['fbid'] = info['id'];
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('kindle-users')
    event['table'] = table

    # run specific handler
    return fn(event)
