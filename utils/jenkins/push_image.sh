#!/bin/bash

set -euo pipefail


# IMAGE_NAME and TARGET_IMAGE defined in jenkins environment
# CHANGE_BRANCH is set on PR, BRANCH_NAME is used on master builds
CURRENT_BRANCH=${CHANGE_BRANCH:-$BRANCH_NAME}

push_image() {
    TARGET_IMAGE="${1}-docker.pkg.dev/${GAR_PROJECT}/${GAR_REPO}/$IMAGE_NAME"
    docker tag "$IMAGE_NAME" "$TARGET_IMAGE":"$GIT_COMMIT"
    docker tag "$IMAGE_NAME" "$TARGET_IMAGE":"$CURRENT_BRANCH"
    # push with commit id tag
    docker push "$TARGET_IMAGE":"$GIT_COMMIT"
    # push with branch name tag
    docker push "$TARGET_IMAGE":"$CURRENT_BRANCH"

    # when building master push with latest tag
    if [ "$CURRENT_BRANCH" = "master" ]; then
        docker tag "$IMAGE_NAME" "$TARGET_IMAGE":latest
        docker push "$TARGET_IMAGE":latest
    fi
}

push_images() {
    IFS=',' read -r -a GAR_REGIONS <<<"$GAR_LOCATIONS"
    for GAR_REGION in "${GAR_REGIONS[@]}"; do
        push_image "$GAR_REGION"
    done
}

push_images
