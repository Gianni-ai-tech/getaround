#!/bin/bash
# Déploiement de l'API sur AWS Lambda (à lancer dans AWS CloudShell, dans le dossier de l'API)
set -euo pipefail
REGION=${AWS_REGION:-eu-west-3}
NOM=getaround-api
COMPTE=$(aws sts get-caller-identity --query Account --output text)
REPO=$COMPTE.dkr.ecr.$REGION.amazonaws.com/$NOM

echo "== 1. Dépôt ECR"
aws ecr describe-repositories --repository-names $NOM --region $REGION >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name $NOM --region $REGION >/dev/null
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $COMPTE.dkr.ecr.$REGION.amazonaws.com

echo "== 2. Image Docker"
docker build --platform linux/amd64 --provenance=false -f Dockerfile.lambda -t $REPO:latest .
docker push $REPO:latest

echo "== 3. Rôle IAM"
if ! aws iam get-role --role-name $NOM-role >/dev/null 2>&1; then
  aws iam create-role --role-name $NOM-role --assume-role-policy-document \
    '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name $NOM-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  sleep 15
fi
ROLE=$(aws iam get-role --role-name $NOM-role --query Role.Arn --output text)

echo "== 4. Fonction Lambda"
if aws lambda get-function --function-name $NOM --region $REGION >/dev/null 2>&1; then
  aws lambda update-function-code --function-name $NOM --image-uri $REPO:latest --region $REGION >/dev/null
else
  aws lambda create-function --function-name $NOM --package-type Image --code ImageUri=$REPO:latest \
    --role $ROLE --memory-size 2048 --timeout 60 --region $REGION >/dev/null
fi
aws lambda wait function-active-v2 --function-name $NOM --region $REGION
aws lambda wait function-updated-v2 --function-name $NOM --region $REGION

echo "== 5. URL publique"
aws lambda get-function-url-config --function-name $NOM --region $REGION >/dev/null 2>&1 || \
  aws lambda create-function-url-config --function-name $NOM --auth-type NONE --region $REGION >/dev/null
aws lambda add-permission --function-name $NOM --statement-id url-public --action lambda:InvokeFunctionUrl \
  --principal "*" --function-url-auth-type NONE --region $REGION >/dev/null 2>&1 || true
aws lambda add-permission --function-name $NOM --statement-id url-invoke --action lambda:InvokeFunction \
  --principal "*" --invoked-via-function-url --region $REGION >/dev/null 2>&1 || true
URL=$(aws lambda get-function-url-config --function-name $NOM --region $REGION --query FunctionUrl --output text)
echo "URL : $URL"

echo "== 6. Test"
sleep 5
curl -s -X POST "${URL}predict" -H "Content-Type: application/json" \
  -d '{"input": [["Citroën", 140411, 100, "diesel", "black", "convertible", true, true, false, false, true, true, true]]}'
echo
curl -s -o /dev/null -w "GET /docs -> %{http_code}\n" "${URL}docs"
