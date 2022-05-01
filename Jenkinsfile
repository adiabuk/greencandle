pipeline {

  agent any

  stages {

    stage("build") {

      steps {
        echo 'building app'
        bash '''
            #!/bin/bash
            echo "hello world"
            ./setup.py install --user
         '''

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

