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
          - name: gps-shell
            image: cavcrosby/gps-shell:latest
            command:
              - cat
            volumeMounts:
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
    stage('Build (python)') {
      when {
        expression {
          "${params.PROGLANG}".toLowerCase() == "python"
        }
      }
      steps {
        container(name: 'gps-python') {
          checkout scm
          sh 'make prefix="${PWD}" VIRTUALENV_PYTHON_VERSION="system" PROGLANG="python" setup'
          sh 'make prefix="${PWD}" PROGLANG="python" install'
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
        container(name: 'gps-shell') {
          checkout scm
          sh 'make prefix="${PWD}" PYENV_SETUP="false" PROGLANG="shell" setup'
          sh 'make prefix="${PWD}" PROGLANG="shell" install'
        }
      }
    }

    stage('Run (python)') {
      when {
        allOf {
          expression {
            currentBuild.result == null || currentBuild.result == 'SUCCESS'
          }
          expression {
            "${params.PIPELINE_MODE}".toLowerCase() == "run"
          }
          expression {
            "${params.PROGLANG}".toLowerCase() == "python"
          }
        }
      }
      steps {
        container(name: 'gps-python') {
          sh './bin/${SCRIPT_NAME} ${SCRIPT_ARGS} <<< "$(./bin/genconfigs --export ${SCRIPT_NAME})"'
        }
      }
    }

    stage('Run (shell)') {
      when {
        // Accessing the currentBuild.result variable allows the pipeline to determine if
        // there were any failures in the previous stages.
        allOf {
          expression {
            currentBuild.result == null || currentBuild.result == 'SUCCESS'
          }
          expression {
            "${params.PIPELINE_MODE}".toLowerCase() == "run"
          }
          expression {
            "${params.PROGLANG}".toLowerCase() == "shell"
          }
        }
      }
      steps {
        container(name: 'gps-shell') {
          sh './bin/${SCRIPT_NAME} ${SCRIPT_ARGS} <<< "$(./bin/genconfigs --export ${SCRIPT_NAME})"'
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