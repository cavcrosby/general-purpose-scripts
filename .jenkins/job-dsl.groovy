pipelineJob ('general-purpose-scripts') {
    
    logRotator {
        numToKeep(5)
    }

    parameters {
        stringParam('SCRIPT_NAME', 'fetch_github_repos.py', 'The name of the script to run.')
        stringParam('SCRIPT_ARGS', '-h', 'The arguments to append to the script, should be a space separated character string (e.g. "--foo bar baz").')
        stringParam('PIPELINE_MODE', 'test', 'The "mode" in which this particular pipeline should run in.')
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
            scriptPath('.jenkins/Jenkinsfile')
        }
    }

    properties {
        pipelineTriggers{
            triggers {
                // TODO(cavcrosby): figure out the desired cron schedule.
                pollSCM{
                    scmpoll_spec('H/5 * * * *')
                }
                parameterizedCron { 
                    parameterizedSpecification('''''')
                }
            }
        }
    }
}
