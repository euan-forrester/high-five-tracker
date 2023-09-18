# high-five-tracker
Tracks mentions in Fraser Health's high fives

### To build

```
terraform init

terraform apply
```

#### Manual steps to push our docker images to ECR

Install docker: https://docs.docker.com/install/

Install the AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/install-bundle.html

Note that you need to create & populate `~/.aws/credentials`

Log into your docker repository:

```
eval "$(aws ecr get-login --no-include-email --region us-west-2)"
```

Then build and push your image:

```
cd src
docker build -f ./Dockerfile .
docker images
docker tag <ID of image you just built> <URI of high-five-tracker-[dev|prod] repository in ECR: use AWS console to find>
docker push <URI of high-five-tracker-[dev|prod] repository in ECR>
```
