.PHONY: ol aws lambda s3 local

ol : lambda local
aws : lambda s3

static/dict.json : parse_wordnet.py
	python parse_wordnet.py > static/dict.json

lambda :
	rm -f lambda.zip
	zip -j -r lambda.zip lambda
	aws lambda update-function-code --function-name=kindle-vocab --zip-file=fileb://lambda.zip

local :
	python update-conf.py ol
	python setup.py

s3 : static/dict.json
	python update-conf.py aws
	aws s3 sync static s3://kindle-vocab
