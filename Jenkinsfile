pipeline {

  agent any

  stages {

    stage("build") {

      steps {
        echo 'building app'
        sh "./setup.py install --user"

      }
    }
    stage("test") {

      steps {
        parallel(
          "assocs": {
          echo "testing assocs"
          sh "./run_tests.sh -v -t assocs"
          },
          "pairs": {
          echo "testing pairs"
          sh "./run_tests.sh -v -t pairs"
          },
          "scripts": {
          echo "testing scripts"
          sh "./run_tests.sh -v -t scripts"
          },
          "lint": {
          echo "testing lint"
          sh "./run_tests.sh -v -t lint"
          },
          "config": {
          echo "testing envs"
          sh "./run_tests.sh -v -t config"
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

