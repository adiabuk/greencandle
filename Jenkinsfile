pipeline {

  agent any
  environment {
    PATH = "/home/jenkins/.local/bin:${env.PATH}"
    DOCKER_HOST = 'tcp://172.17.0.1:2375'
  }

  stages {

    stage("build") {

      steps {
        echo 'building app'
        sh "./setup.py install --user"

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
              sh "./run_tests.py -v -t assocs"
            }
          },
          "mysql": {
            echo "testing mysql"
            ansiColor('Vga') {
                  build job: 'docker-pipe2', parameters: [string(name: 'version',
                  value:'jenkins_test'), string(name:'test', value: "mysql")]
            }
          },
          "redis": {
            echo "testing redis"
            ansiColor('Vga') {
                  build job: 'docker-pipe2', parameters: [string(name: 'version',
                  value:'jenkins_test'), string(name:'test', value: "redis")]
            }
          },
          "docker": {
            echo "testing docker"
            ansiColor('Vga') {
                  build job: 'docker-pipe2', parameters: [string(name: 'version',
                  value:'jenkins_test'), string(name:'test', value: "docker")]
            }
          },
          "stop": {
            echo "testing stop"
            ansiColor('Vga') {
                  build job: 'docker-pipe2', parameters: [string(name: 'version',
                  value:'jenkins_test'), string(name:'test', value: "stop")]
            }
          },
          "draw": {
            echo "testing draw"
            ansiColor('Vga') {
                  build job: 'docker-pipe2', parameters: [string(name: 'version',
                  value:'jenkins_test'), string(name:'test', value: "draw")]
            }
          },
          "pairs": {
            echo "testing pairs"
            ansiColor('vga') {
              sh "./run_tests.py -v -t pairs"
            }
          },
          "scripts": {
            echo "testing scripts"
            sh "echo $PATH"
            ansiColor('vga') {
              sh "./run_tests.py -v -t scripts"
            }
          },
          "lint": {
            echo "testing lint"
            ansiColor('vga') {
              sh "./run_tests.py -v -t lint"
            }
          },
          "config": {
            echo "testing envs"
            ansiColor('vga') {
              sh "./run_tests.py -v -t config"
            }
          })

      }
    }

    stage("deploy") {

      steps {
        echo 'deploy app'
      }
    }

  }

}
