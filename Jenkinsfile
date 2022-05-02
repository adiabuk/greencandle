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
          "lint": {
          echo "testing lint"
          },
          "config": {
          echo "testing config"
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

