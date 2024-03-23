pipeline {
  agent {
    kubernetes {
      yaml '''
        apiVersion: v1
        kind: Pod
        metadata:
          labels:
            jenkins-agent: gps-build-agent
        spec:
          securityContext:
            runAsUser: 1000
          containers:
          - name: gps-python
            image: cavcrosby/gps-python:latest
            command:
              - cat
            volumeMounts:
              - name: github-ssh-secret
                mountPath: /home/runner/.ssh/id_rsa_github
              - name: gps-configs-secret
                mountPath: /usr/local/etc
            env:
              - name: GPS_CONFIG_FILE_PATH
                value: /usr/local/etc/gps.json
            tty: true
          volumes:
            - name: github-ssh-secret
              secret:
                secretName: github-ssh-key
                items:
                  - key: id_rsa_github
                    path: id_rsa_github
            - name: gps-configs-secret
              secret:
                secretName: gps-configs
                items:
                  - key: gps.json
                    path: gps.json
      '''
    }
  }

  stages {
    stage('Run (python)') {
      when {
        expression {
          "${params.PROGLANG}".toLowerCase() == "python"
        }
      }
      steps {
        container(name: 'gps-python') {
          checkout scm
          sh 'make setup'
          sh './src/${SCRIPT_NAME} ${SCRIPT_ARGS} <<< "$(./bin/genconfigs --export ${SCRIPT_NAME})"'
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
