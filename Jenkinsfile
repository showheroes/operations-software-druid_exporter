def buildImage() {
    sh 'gcloud auth activate-service-account --key-file=${GCE_SERVICE_ACCOUNT_KEY}'
    sh 'gcloud auth configure-docker'
    sh 'docker build -t "$TARGET_IMAGE" .'
    sh 'utils/jenkins/push_image.sh'
}

pipeline {
    agent { label "jnlp_dind_kubectl" }

    environment {
        CLOUDSDK_PYTHON = "/usr/bin/python"
        GCP_PROJECT_ID = "viralize-ci"
        IMAGE_NAME = "eu.gcr.io/$GCP_PROJECT_ID/prometheus-druid-exporter"
        TARGET_IMAGE = "$IMAGE_NAME:$GIT_COMMIT"
        GCE_SERVICE_ACCOUNT_KEY = credentials('CI_GCR_SERVICE_ACCOUNT')
    }

    stages {
        stage('Build') {
            steps {
                script {
                    buildImage()
                }
            }
        }
    }
}
