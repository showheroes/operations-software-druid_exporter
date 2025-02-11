def gcloudInit() {
  sh "gcloud auth activate-service-account --key-file='${GCE_SERVICE_ACCOUNT_KEY}'"
  GAR_LOCATIONS.split(',').each { l ->
    sh "gcloud auth configure-docker ${l}-docker.pkg.dev"
  }
}

def buildImage() {
    sh '''
          docker buildx build \
            --cache-to type=inline \
            --cache-from $CACHE_FROM_IMAGE:latest \
            -t "$IMAGE_NAME" .
        '''
    sh 'utils/jenkins/push_image.sh'
}

pipeline {
    agent { label "jnlp_dind_buildx" }

    environment {
        GCE_SERVICE_ACCOUNT_KEY = credentials('JENKINS_GCP_SA_KEY')
        GAR_PROJECT = "viralize-143916"
        GAR_REPO = "infra"
        GAR_LOCATIONS = "europe,us"
        CACHE_GAR_LOCATION = "europe"
        CACHE_FROM_IMAGE = "${CACHE_GAR_LOCATION}-docker.pkg.dev/${GAR_PROJECT}/${GAR_REPO}/${IMAGE_NAME}"
        IMAGE_NAME = "prometheus-druid-exporter"
        CLOUDSDK_PYTHON = "/usr/bin/python"
    }

    stages {
        stage('GCloud Init') {
            steps {
                script {
                    gcloudInit()
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    buildImage()
                }
            }
        }
    }
}
