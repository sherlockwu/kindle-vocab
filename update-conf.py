#!/usr/bin/env python
import os, sys, json

def main():
    assert(len(sys.argv) == 2)
    backend = sys.argv[1]
    url = {'ol': 'http://162.243.56.233:32769/runLambda/ubcaabfsawdx',
           'aws': 'https://4pcltxpssg.execute-api.us-east-1.amazonaws.com/prod/kindle-vocab'}[backend]
    with open('static/config.json', 'w') as f:
        f.write(json.dumps({'url': url}))

if __name__ == '__main__':
    main()
