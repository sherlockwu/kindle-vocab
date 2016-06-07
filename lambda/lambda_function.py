import sqlite3, base64, tempfile, os, traceback, urllib2, json

class DB:
    def __init__(self):
        pass

class DatabaseIF:
    def __init__(self):
        raise NotImplementedError()

class DynamoDB(DB):
    def __init__(self):
        assert(0)

    def append(self, row_key, col_key, value):
        return
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

    def get(self, row_key):
        pass

    def put(self, row_key, row):
        pass

class RethinkDB(DB):
    def __init__(self, conn, dbname, tablename):
        import rethinkdb as r
        self.conn = conn
        self.table = r.db(dbname).table(tablename)

    def append(self, rowkey, colkey, value):
        table = self.table
        # not atomic!
        lst = table.get(rowkey)[colkey].run(self.conn)
        lst.append(value)
        return table.get(rowkey).update({colkey: lst}).run(self.conn)

    def get(self, rowkey):
        return self.table.get(rowkey).run(self.conn)

    def put(self, row):
        return self.table.insert(row, conflict='replace').run(self.conn)

def update_user(event, words):
    # insert words in dynamodb
    table = event['table']
    user = {'fbid': event['fbid'],
            'words': words,
            'practice': []}
    return table.put(user)

def practice(event):
    table = event['table']
    assert(len(event['cur_words']) <= 10)
    for w in event['cur_words']:
        assert(isinstance(w, basestring))
        assert(len(w) < 255)
    assert(event['guess'] in event['cur_words'])
    assert(event['actual'] in event['cur_words'])
    row = {'cur_words': event['cur_words'],
	   'guess':     event['guess'],
	   'actual':    event['actual']};
    return table.append(event['fbid'], 'practice', row)

def fetch_words(event):
    table = event['table']
    row = table.get(event['fbid'])
    if row == None:
        update_user(event, [])
    row = table.get(event['fbid'])
    return row['words']

def upload(event):
    fd, path = tempfile.mkstemp(suffix='.db')
    f = os.fdopen(fd, 'wb')
    f.write(base64.b64decode(event['db']))
    f.close()
    conn = sqlite3.connect(path)
    words = [row[0] for row in conn.execute('SELECT word FROM words')]
    return update_user(event, words);

def stats(event):
    table = event['table']
    user = table.get(event['fbid'])

    correct = 0
    wrong = 0
    for row in user['practice']:
        if row['actual'] == row['guess']:
            correct += 1
        else:
            wrong += 1
    rv = [
        {'name': 'correct', 'val': correct},
        {'name': 'wrong', 'val': wrong}
    ]
    return rv

# aws entry
def lambda_handler(event, context):
    import boto3

    fn = {
        'upload': upload,
        'fetch_words': fetch_words,
        'practice': practice,
        'stats': stats,
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

def handler(conn, event):
    fn = {
        'upload': upload,
        'fetch_words': fetch_words,
        'practice': practice,
        'stats': stats,
    }[event['op']]
    event['table'] = RethinkDB(conn, 'vocab', 'kindle_users')

    # run specific handler
    return fn(event)
