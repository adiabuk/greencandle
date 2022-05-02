pipeline {

  agent any

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
        sh "configstore package process_templates unit /etc"
      }
    }
    stage("test") {

      steps {
        parallel(
          "assocs": {
          echo "testing assocs"
          sh "./run_tests.py -v -t assocs"
          },
          "pairs": {
          echo "testing pairs"
          sh "./run_tests.py -v -t pairs"
          },
          "scripts": {
          echo "testing scripts"
          sh "./run_tests.py -v -t scripts"
          },
          "lint": {
          echo "testing lint"
          sh "./run_tests.py -v -t lint"
          },
          "config": {
          echo "testing envs"
          sh "./run_tests.py -v -t config"
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

