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
          sh "sleep 500"
          },
          "config": {
          echo "testing config"
          sh "sleep 1000"
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

