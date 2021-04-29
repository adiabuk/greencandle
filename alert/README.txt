Manual image build steps:
docker build -f install/Dockerfile-as .
docker tag <image_id> amrox/alert:latest
docker push amrox/alert:latest
