pipeline {

  agent any
environment {
    PATH = "/home/jenkins/.local/bin:${env.PATH}"
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
          ansiColor('xterm'){
          sh "./run_tests.py -v -t assocs"}
          },
          "pairs": {
          echo "testing pairs"
          ansiColor('xterm'){
          sh "./run_tests.py -v -t pairs"
          }
          },
          "scripts": {
          echo "testing scripts"
          sh "echo $PATH"
          ansiColor('xterm'){
          sh "./run_tests.py -v -t scripts"
          }
          },
          "lint": {
          echo "testing lint"
          ansiColor('xterm'){
          sh "./run_tests.py -v -t lint"
          }
          },
          "config": {
          echo "testing envs"
          ansiColor('xterm'){
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

