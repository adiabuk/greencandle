pipeline {
    agent any
    environment {
        PATH = "/home/jenkins/.local/bin:${env.PATH}"
        DOCKER_HOST = "unix:///var/run/docker.sock"
        image_id = "${env.BUILD_ID}"
        GIT_REPO_NAME = env.GIT_URL.replaceFirst(/^.*?(?::\/\/.*?\/|:)(.*).git$/, '$1')
        SHORT_COMMIT = "${GIT_COMMIT[0..7]}"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        disableConcurrentBuilds()
        buildBlocker (useBuildBlocker: true, blockLevel: 'GLOBAL', scanQueueFor: 'DISABLED', blockingJobs: '.*')
        timeout(time: 1, unit: 'HOURS')
    }

    stages {
        stage("Start") {
            steps {
                slackSend color: "#808080", message: "Starting build\nRepo: ${env.GIT_REPO_NAME}\nCommit: ${SHORT_COMMIT}\nBranch: ${env.GIT_BRANCH}\nURL: (<${env.BUILD_URL}|Open>)"
            }
        }
        stage("Mute Nagios Notifications") {
            steps {
                 build(job: 'nagios-downtime', parameters:
                            [string(name: 'TIME', value: "12"),
                             string(name: 'COMMENT', value: "running+build")])
            }
        }
        stage("build docker images") {
            steps {
                echo 'building apps'
                //sh "sudo ln -s . /srv/greencandle"
                ansiColor('vga') {
                     sh 'git checkout $SHORT_COMMIT'
                     sh 'docker-compose -f install/docker-compose_jenkins.yml -p $BUILD_ID build --build-arg BRANCH=$GIT_BRANCH --build-arg COMMIT=$SHORT_COMMIT --build-arg DATE="$(date)"'
                     //sh 'docker pull amrox/alert; docker tag amrox/alert alert-${image_id}'
                 }
             }
        }
        stage("run tests") {
            steps {
                echo "run all tests"
                ansiColor('vga') {
                    build job: 'all-tests', parameters:
                    [string(name: 'version', value: env.GIT_BRANCH),
                     string(name: 'commit', value: env.GIT_COMMIT),
                     string(name: 'image_id', value: env.BUILD_ID)
                     ]
                }
            }
        }
        stage("Push to registry") {
            steps {
                echo "pushing all"
                ansiColor('vga') {
                    build job: 'all-push', parameters:
                    [string(name: 'version', value: env.GIT_BRANCH),
                     string(name: 'commit', value: env.GIT_COMMIT),
                     string(name: 'image_id', value: env.BUILD_ID)
                     ]
                }
            }
        }
        stage("cleanup network") {
            steps {
                echo 'cleaning up unused docker networks'
                sh "sudo docker network prune -f || true"
                 }
        }
    }

    post {
        always {
            sh """
            docker-compose -f install/docker-compose_jenkins.yml -p $BUILD_ID down --rmi all
            docker network prune -f
            """
        }
        success {
            slackSend color: "good", message: "Repo: ${env.GIT_REPO_NAME}\nResult: ${currentBuild.currentResult}\nCommit: ${SHORT_COMMIT}\nBranch: ${env.GIT_BRANCH}\nExecution time: ${currentBuild.durationString.replace(' and counting', '')}\nURL: (<${env.BUILD_URL}|Open>)"
        }
        failure { slackSend color: "danger", message: "Repo: ${env.GIT_REPO_NAME}\nResult: ${currentBuild.currentResult}\nCommit: ${SHORT_COMMIT}\nBranch: ${env.GIT_BRANCH}\nExecution time: ${currentBuild.durationString.replace(' and counting', '')}\nURL: (<${env.BUILD_URL}|Open>)"
        }
    }
}
