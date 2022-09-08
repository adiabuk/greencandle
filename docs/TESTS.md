
# Testing

* Jenkins testing

Jenkins tests are triggered automatically shortly after a commit is pushed
Tests and builds for git tags need to be triggered manually in the UI

* Local testing
Use the following to trigger a test locally

cd /srv/greencandle
python setup.py install
TAG=latest image=latest docker-compose -f install/docker-compose_dev.yml up -d
image_id=1 test=<test_name> ./run_tests.py -v -t <test_name>
