pipeline {

  agent any

  stages {

    stage("build") {

      steps {
        echo 'building app'
        ./setup.py install --user
      }
    }
    stage("test") {

      steps {
        echo 'testing app'
      }
    }

    stage("deploy") {

      steps {
        echo 'deploy app'
      }
    }


  }



}

