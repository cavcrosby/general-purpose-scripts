pipelineJob ('gps-container-images') {
    
    logRotator {
        numToKeep(5)
    }

    parameters {
        stringParam('PROGLANG', 'python', 'The programming language that a container image is prepared for.')
    }

    definition {
        cpsScm {
            scm {
                git {
                    branch('main')
                    remote {
                        credentials(System.getenv('JENKINS_GITHUB_CREDENTIAL_ID') ?: '')
                        url('https://github.com/cavcrosby/general-purpose-scripts')
                    }
                }
            }
            scriptPath('./.jenkins/gps-container-images.Jenkinsfile')
        }
    }

    properties {
        pipelineTriggers {
            triggers {
                parameterizedCron {
                    parameterizedSpecification('''
                        H(0-10) 5 */2 * * % PROGLANG=python;
                    ''')
                }
            }
        }
    }
}

pipelineJob ('general-purpose-scripts') {
    
    logRotator {
        numToKeep(5)
    }

    parameters {
        stringParam('SCRIPT_NAME', 'update_github_forks.py', 'The name of the script to run.')
        stringParam('SCRIPT_ARGS', '-h', 'The arguments to append to the script, should be a space separated character string (e.g. "--foo bar baz").')
        stringParam('PROGLANG', 'python', 'The programming language the script was written in.')
    }

    definition {
        cpsScm {
            scm {
                git {
                    branch('main')
                    remote {
                        credentials(System.getenv('JENKINS_GITHUB_CREDENTIAL_ID') ?: '')
                        url('https://github.com/cavcrosby/general-purpose-scripts')
                    }
                }
            }
            scriptPath('./.jenkins/general-purpose-scripts.Jenkinsfile')
        }
    }

    properties {
        pipelineTriggers{
            triggers {
                pollSCM{
                    scmpoll_spec('H/5 * * * *')
                }
                parameterizedCron {
                    // hour field assumes time zone is UTC
                    //
                    // Also, the spacing is retained when viewing the parameterized cron jobs
                    // through Jenkins. Not pretty to look at but I am ok with this.
                    parameterizedSpecification('''
                        H(0-5) 8 * * * % SCRIPT_NAME=update_remote_forks.py; SCRIPT_ARGS=--stdin --verbose; PROGLANG=python;
                        H(15-20) 8 * * * % SCRIPT_NAME=disable_github_actions.py; SCRIPT_ARGS=--stdin; PROGLANG=python;
                    ''')
                }
            }
        }
    }
}
