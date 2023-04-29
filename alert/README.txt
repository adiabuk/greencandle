Manual image build steps:
docker build -f install/Dockerfile-as . -t amrox/alert:latest
docker push amrox/alert:latest
