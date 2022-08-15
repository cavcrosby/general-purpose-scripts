pipeline {
  agent {
    kubernetes {
      yaml '''
        apiVersion: v1
        kind: Pod
        metadata:
          labels:
            jenkins-agent: kaniko
        spec:
          securityContext:
            runAsUser: 0
          containers:
          - name: kaniko
            image: gcr.io/kaniko-project/executor:debug
            command:
              - cat
            volumeMounts:
              - name: dockerhub-secret
                mountPath: /kaniko/.docker
            tty: true
          volumes:
            - name: dockerhub-secret
              secret:
                secretName: dockerhub-creds
                items:
                  - key: .dockerconfigjson
                    path: config.json
      '''
    }
  }

  stages {
    stage('Build (python)') {
      when {
        expression {
          "${params.PROGLANG}".toLowerCase() == "python"
        }
      }
      steps {
        container(name: 'kaniko') {
          checkout scm
          sh '''#!/bin/sh
            /kaniko/executor \
              --context "${PWD}" \
              --dockerfile "./dockerfiles/gps-python.Dockerfile" \
              --destination "cavcrosby/gps-python:latest"
          '''
        }
      }
    }

    stage('Build (shell)') {
      when {
        expression {
          "${params.PROGLANG}".toLowerCase() == "shell"
        }
      }
      steps {
        container(name: 'kaniko') {
          sh '''#!/bin/sh
            /kaniko/executor \
              --context "${PWD}" \
              --dockerfile "./dockerfiles/gps-shell.Dockerfile" \
              --destination "cavcrosby/gps-shell:latest"
          '''
        }
      }
    }
  }

  post {
    failure {
      emailext body: 'Check console output at ${BUILD_URL} to view the results. \n\n ${CHANGES} \n -------------------------------------------------- \n${BUILD_LOG, maxLines=100, escapeHtml=false}',
               from: "Jenkins Build Notifications <" + (System.getenv('JENKINS_ADMIN_EMAIL') ?: "") + ">",
               to: System.getenv('JENKINS_ADMIN_EMAIL') ?: "",
               subject: "Build failed in Jenkins: ${JOB_NAME} - #${BUILD_NUMBER}"
    }
    cleanup {
      cleanWs()
    }
  }
}
