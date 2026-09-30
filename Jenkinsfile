// Same pipeline as GitHub Actions, written for Jenkins.
// Shows the equivalent stages: checkout -> lint -> test -> triage -> publish.
pipeline {
    agent any

    options {
        timeout(time: 20, unit: 'MINUTES')
    }

    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Build image') {
            steps { sh 'docker compose build' }
        }
        stage('Lint') {
            steps { sh 'docker compose run --rm tests flake8' }
        }
        stage('Test') {
            steps {
                sh 'docker compose up --abort-on-container-exit --exit-code-from tests'
            }
        }
    }

    post {
        always {
            sh 'docker compose run --rm -e ANTHROPIC_API_KEY tests python tools/ai_triage.py reports/junit.xml || true'
            junit 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/**, artifacts/**', allowEmptyArchive: true
            sh 'docker compose down'
        }
    }
}
