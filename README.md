# sample-python-app (NON WSGI / NOT FOR PRODUCTION)

docker rmi -f $(docker images -q)
docker system prune -a --volumes

ssh -i capital-one.pem ubuntu@ec2-34-239-105-87.compute-1.amazonaws.com

docker build -f Dockerfile.app -t capital-one-server-image:latest .

docker run -d --name capital-one-1 -p 8080:8080 capital-one-server-image:latest