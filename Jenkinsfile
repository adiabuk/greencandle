pipeline {

    agent any
    environment {
        PATH = "/home/jenkins/.local/bin:${env.PATH}"
        DOCKER_HOST = 'tcp://172.17.0.1:2375'
        image_id = "${env.BUILD_ID}"
    }

    stages {

        stage("build") {

            steps {
                sh "env"
                echo 'building apps'
                //sh "./setup.py install --user"
                ansiColor('vga') {
                  sh 'docker-compose -f docker-compose_jenkins.yml -p $BUILD_ID build'
                        }
            }
        }
        stage("prepare") {
            steps {
                echo "preparing env"
                sh "sudo configstore package process_templates unit /etc"
                sh "sudo ln -s `pwd` /srv/greencandle"

            }
        }
        stage("test") {

            steps {
                parallel(
                    "assocs": {
                        echo "testing assocs"
                        ansiColor('vga') {
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "assocs"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]

                        }
                    },
                    "mysql": {
                        echo "testing mysql"
                        ansiColor('Vga') {
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "mysql"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "redis": {
                        echo "testing redis"
                        ansiColor('Vga') {
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "redis"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "docker": {
                        echo "testing docker"
                        ansiColor('Vga') {
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "docker"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "stop": {
                        echo "testing stop"
                        ansiColor('Vga') {
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "stop"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "draw": {
                        echo "testing draw"
                        ansiColor('Vga') {
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "draw"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "pairs": {
                        echo "testing pairs"
                        ansiColor('vga') {
                            //sh "./run_tests.py -v -t pairs"
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "pairs"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]

                        }
                    },
                    "scripts": {
                        echo "testing scripts"
                        sh "echo $PATH"
                        ansiColor('vga') {
                            //sh "./run_tests.py -v -t scripts"
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "scripts"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]

                        }
                    },
                    "lint": {
                        echo "testing lint"
                        ansiColor('vga') {
                            //sh "./run_tests.py -v -t lint"
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "lint"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]

                        }
                    },
                    "config": {
                        echo "testing envs"
                        ansiColor('vga') {
                            //sh "./run_tests.py -v -t config"
                            build job: 'docker-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "config"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]

                        }
                    })

            }
        }

        stage("deploy") {

            steps {
                parallel(
                    "greencandle": {
                        ansiColor('vga') {
                            build job: 'docker-build', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                            string(name: 'app', value: "greencandle"),
                            string(name: 'image_id', value: env.BUILD_ID)
                            ]
                        }
                    },
                    "mysql": {
                        ansiColor('vga') {
                            build job: 'docker-build', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                            string(name: 'app', value: "mysql"),
                            string(name: 'image_id', value: env.BUILD_ID)
                            ]
                        }
                    },
                    "redis": {
                        ansiColor('vga') {
                            build job: 'docker-build', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                            string(name: 'app', value: "redis"),
                            string(name: 'image_id', value: env.BUILD_ID)
                            ]
                        }
                    },
                    "web": {
                        ansiColor('vga') {
                            build job: 'docker-build', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                            string(name: 'app', value: "web"),
                            string(name: 'image_id', value: env.BUILD_ID)
                            ]
                        }
                    },
                    "alert": {
                        ansiColor('vga') {
                            build job: 'docker-build', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                            string(name: 'app', value: "alert"),
                            string(name: 'image_id', value: env.BUILD_ID)
                            ]
                        }
                    }
                )
            }
        }
    }
    post {
        success {
            slackSend color: "good", message: "branch ${env.BRANCH_NAME} completed successfully after ${currentBuild.durationString}"
        }
        failure {
            slackSend color: "bad", message: "branch ${env.BRANCH_NAME} failed after ${currentBuild.durationString}"
        }
    }
}
