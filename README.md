# napapp

## Start

```sh
cp .env.example .env
minikube start
kubectl create secret generic mongo-secret --from-env-file=.env
kubectl apply -f napapp-v1.yml
kubectl get pods -w
minikube service web
```

## Stop

```sh
kubectl delete -f napapp-v1.yml
kubectl delete secret mongo-secret
minikube stop
```
