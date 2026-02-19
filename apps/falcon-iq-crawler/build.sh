#!/bin/bash

# Build script for Falcon IQ Crawler Docker image
# Usage: ./build.sh [tag] [push]
# Example: ./build.sh v1.0.0 push

set -e

IMAGE_NAME="falcon-iq-crawler"
REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
TAG="${1:-latest}"
SHOULD_PUSH="${2}"

echo "Building Falcon IQ Crawler Docker image..."

echo "Building image: ${IMAGE_NAME}:${TAG}"
docker build -t ${IMAGE_NAME}:${TAG} .

if [ ! -z "$REGISTRY" ]; then
    echo "Tagging for registry: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
    docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:${TAG}
fi

echo "Build completed successfully!"

if [ "$SHOULD_PUSH" = "push" ]; then
    if [ -z "$REGISTRY" ]; then
        echo "Cannot push: AWS_ACCOUNT_ID and AWS_REGION environment variables must be set"
        exit 1
    fi

    echo "Logging into ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${REGISTRY}

    echo "Pushing image to ECR..."
    docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}

    echo "Image pushed successfully!"
    echo "Image URI: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
fi

echo "Done!"
