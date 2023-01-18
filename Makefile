TEMPLATE_FILE = ./src/cloudformation-template.yml
STACK_NAME = data-transfer-test
LAMBDA_RESOURCES_BUCKET = lambda-resources-665378081513
BUCKET = cfn-build-objects
PREFIX = lambda-totp-s3
PROFILE = tohi.work-admin
PARAMETERS = ./src/params/parameter.dev.json


test:
	aws s3 cp test.txt s3://data-receive-sample/data/ --profile $(PROFILE)

package:
	mkdir -p build
	zip -j ./build/lambda_function.zip ./src/lambda_function/index.py
	zip -r ./build/mfa.zip ./python/

	aws cloudformation package --template-file $(TEMPLATE_FILE) \
		--s3-bucket $(BUCKET) \
		--s3-prefix $(PREFIX) \
		--output-template-file build/cloudformation-template.yml \
		--region ap-northeast-1 \
		--profile $(PROFILE)

deploy:
	aws cloudformation deploy --template-file ./build/cloudformation-template.yml \
	--stack-name $(STACK_NAME) \
	--region ap-northeast-1 --profile $(PROFILE) \
	--capabilities CAPABILITY_NAMED_IAM \
	--parameter-overrides `cat $(PARAMETERS) | jq -r '.Parameters | to_entries | map("\(.key)=\(.value|tostring)") | .[]' | tr '\n' ' ' | awk '{print}'`

validate:
	aws cloudformation validate-template --template-body file://src/cloudformation/cloudformation-template.yml

all: package deploy

confirm:
	@read -p "Delete $(STACK_NAME) ?[y/N]: " ans; \
        if [ "$$ans" != y ]; then \
                exit 1; \
        fi

delete: confirm
	aws cloudformation delete-stack \
	--stack-name $(STACK_NAME) \
	--region ap-northeast-1 \
	--profile $(PROFILE)\
