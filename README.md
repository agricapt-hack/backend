# sample-python-app (NON WSGI / NOT FOR PRODUCTION)
ssh -i capital-one.pem ubuntu@ec2-34-239-105-87.compute-1.amazonaws.com

docker kill capital-one-1 || echo " capital-one-1 cannot be killed "
docker rmi -f $(docker images -q)
docker system prune -a --volumes
docker build -f Dockerfile.app -t capital-one-server-image:latest .
docker run -d --name capital-one-1 -p 8080:8080 capital-one-server-image:latest