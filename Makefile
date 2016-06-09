AWS_URL = https://4pcltxpssg.execute-api.us-east-1.amazonaws.com/prod/kindle-vocab

.PHONY: aws aws-s3 aws-lambda
.PHONY: ol ol-lambda ol-static

# common to AWS and OL
static/dict.json : parse_wordnet.py
	python parse_wordnet.py > static/dict.json

# AWS stuff
aws : aws-s3 aws-lambda

aws-lambda :
	rm -f lambda.zip
	zip -j -r lambda.zip lambda
	aws lambda update-function-code --function-name=kindle-vocab --zip-file=fileb://lambda.zip

aws-s3 : static/dict.json
	echo '{"url": "$(AWS_URL)"}' > static/config.json
	aws s3 sync static s3://kindle-vocab

# OL stuff
ol : ol-lambda ol-static

ol-lambda :
	python setup.py

ol-static :
	./ol-serve-static.sh nginx-vocab
