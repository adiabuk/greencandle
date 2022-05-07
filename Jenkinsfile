pipeline {

    agent any
    environment {
        PATH = "/home/jenkins/.local/bin:${env.PATH}"
        DOCKER_HOST = 'tcp://172.17.0.1:2375'
        image_id = "${env.BUILD_ID}"
        GIT_REPO_NAME = env.GIT_URL.replaceFirst(/^.*\/([^\/]+?).git$/, '$1')
    }

    stages {
        stage("build docker images") {
            steps {
                sh "env"
                echo 'building apps'
                ansiColor('vga') {
                  sh 'docker-compose -f docker-compose_jenkins.yml -p $BUILD_ID build'
                        }
            }
        }

        stage("run unittests") {
            steps {
                parallel(
                    "assocs": {
                        echo "testing assocs"
                        ansiColor('vga') {
                            build job: 'unit-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "assocs"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]

                        }
                    },
                    "mysql": {
                        echo "testing mysql"
                        ansiColor('Vga') {
                            build job: 'unit-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "mysql"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "redis": {
                        echo "testing redis"
                        ansiColor('Vga') {
                            build job: 'unit-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "redis"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "docker-mysql": {
                        echo "testing docker-mysql"
                        ansiColor('Vga') {
                            build job: 'unit-tests', parameters:
                            [string(name: 'version', value: env.GIT_BRANCH),
                             string(name: 'test', value: "docker_mysql"),
                             string(name: 'image_id', value: env.BUILD_ID)
                             ]
                        }
                    },
                    "docker-redis": {
                                    echo "testing docker-redis"
                                    ansiColor('Vga') {
                                        build job: 'unit-tests', parameters:
                                        [string(name: 'version', value: env.GIT_BRANCH),
                                         string(name: 'test', value: "docker_redis"),
                                         string(name: 'image_id', value: env.BUILD_ID)
                                         ]
                                    }
                                },
                    "docker-cron": {
                                    echo "testing docker-cron"
                                    ansiColor('Vga') {
                                        build job: 'unit-tests', parameters:
                                        [string(name: 'version', value: env.GIT_BRANCH),
                                         string(name: 'test', value: "docker_cron"),
                                         string(name: 'image_id', value: env.BUILD_ID)
                                         ]
                                      }
                      },
                    "docker-api": {
                                    echo "testing docker-api"
                                    ansiColor('Vga') {
                                        build job: 'unit-tests', parameters:
                                        [string(name: 'version', value: env.GIT_BRANCH),
                                         string(name: 'test', value: "docker_api"),
                                         string(name: 'image_id', value: env.BUILD_ID)
                                         ]
                                    }
                                },
                      "stop": {
                          echo "testing stop"
                          ansiColor('Vga') {
                              build job: 'unit-tests', parameters:
                              [string(name: 'version', value: env.GIT_BRANCH),
                               string(name: 'test', value: "stop"),
                               string(name: 'image_id', value: env.BUILD_ID)
                               ]
                          }
                      },
                      "draw": {
                          echo "testing draw"
                          ansiColor('Vga') {
                              build job: 'unit-tests', parameters:
                              [string(name: 'version', value: env.GIT_BRANCH),
                               string(name: 'test', value: "draw"),
                               string(name: 'image_id', value: env.BUILD_ID)
                               ]
                          }
                      },
                      "pairs": {
                          echo "testing pairs"
                          ansiColor('vga') {
                              build job: 'unit-tests', parameters:
                              [string(name: 'version', value: env.GIT_BRANCH),
                               string(name: 'test', value: "pairs"),
                               string(name: 'image_id', value: env.BUILD_ID)
                               ]

                          }
                      },
                      "scripts": {
                          echo "testing scripts"
                          ansiColor('vga') {
                              build job: 'unit-tests', parameters:
                              [string(name: 'version', value: env.GIT_BRANCH),
                               string(name: 'test', value: "scripts"),
                               string(name: 'image_id', value: env.BUILD_ID)
                               ]

                          }
                      },
                      "lint": {
                          echo "testing lint"
                          ansiColor('vga') {
                              build job: 'unit-tests', parameters:
                              [string(name: 'version', value: env.GIT_BRANCH),
                               string(name: 'test', value: "lint"),
                               string(name: 'image_id', value: env.BUILD_ID)
                               ]

                          }
                      },
                      "config": {
                          echo "testing envs"
                          ansiColor('vga') {
                              build job: 'unit-tests', parameters:
                              [string(name: 'version', value: env.GIT_BRANCH),
                               string(name: 'test', value: "config"),
                               string(name: 'image_id', value: env.BUILD_ID)
                               ]

                          }
                      }
                  )
             }
        }

        stage("Push to registry") {
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
            slackSend color: "good", message: "Repo: ${env.GIT_REPO_NAME} completed successfully\nCommit: ${env.GIT_COMMIT}\nBranch: ${env.GIT_BRANCH}\nExecution time: ${currentBuild.durationString}\nCurrent result: ${currentBuild.currentResult}"

        }
        failure {
            slackSend color: "danger", message: "Repo: ${env.GIT_REPO_NAME} has failed\nCommit: ${env.GIT_COMMIT}\nBranch: ${env.GIT_BRANCH}\nExecution time: ${currentBuild.durationString}\nCurrent result:${currentBuild.currentResult}"
        }
        always {
            sh 'docker-compose -f docker-compose_jenkins.yml -p $BUILD_ID down --rmi all'
            sh 'docker network prune -f'
        }
    }
}
