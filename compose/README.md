# Docker Compose Service Deployment

## Background
These files are used for `docker compose` deployments of vLLM instances and accompanying services
for the marketagents simulation. This directory contains compose files - one for each host - as well as 
associated configurations. 

To run this, this repository must be cloned on both hosts, and both hosts must be 
joined in a single docker swarm. 

Currently, this repo is cloned on both hosts at `/home/ubuntu/blacklight/Distributed-Infrastructure`.

We are _not_ deploying with swarm, since it does not 
have good GPU support, but we are using it's flat networking overlay to make 
deployment and management easier. 

### Docker Networking
Docker swarm setup has already been performed. Two docker swarm networks were created:
- `distributed-inference-secure` (encrypted -> recommended)
- `distributed-inference` (unencrypted -> not recommended)

Both compose files have been configured to use this overlay network with the `networks` configuration
in the `docker-compose.yml` file. It is **external** meaning it was created outside of the compose file, 
and the compose file should not attempt to create it, but should attach to the existing network:

```yaml
networks:
  distributed-inference-secure:
    external: true
```

**Make sure to include the network for each container in each compose file, like so:**
```yaml 
networks: 
  - distributed-inference-secure
```

Hosts on this network can talk to each other across the network _without_ exposing mapped ports with the `ports` option.

This will also allow us to securely use things like `prometheus`, `redis` and `vllm` that have a "do not put on the public internet without additional configuration" 
security model; and will make postgres access easier as well. 

vLLM instances can avoid having public ports (unless desired) and we can expose them (with authentication)
through LiteLLM or TensorZero. 

Recommended hosts to give public ports:
- `grafana`
- `litellm` (or tensorzero, whatever)
- `postgres` IFF we add a secure password and need access to pull data

**Important**: in order for containers created through compose files to be able to access `docker swarm`-created networks,
you need to use the `compose` plugin for the docker CLI (e.g. `docker compose` instead of `docker-compose`) since `docker-compose` 
is not aware of docker swarm networks, while the regular `docker` CLI with the compose plugin is. 

The `compose` plugin for both hosts has been installed already, but if you are running this on different hosts, you will 
need to install this plugin. Details [here](https://docs.docker.com/compose/install/linux/#install-using-the-repository).
### Jumping in 
To get on the docker network and to be able to touch hosts that aren't exposing ports, I recommend
using `ubuntu:slim`: 

```shell
sudo docker run \
--network distributed-inference-secure \
-it \ # launch shell
debian:12-slim
```
This will let you touch hosts (e.g. through cURL) that are on the docker network using their image name. For example, you 
can run `curl http://prometheus:9090` (NOTE: depending on the image you use, you may need to install tools e.g. cURL, 
postgres client, etc. with `apt-get update` and `apt-get install`)

e.g. 
```shell 
apt-get install curl inetutils-ping
ping prometheus
curl http://vllm-1-qwen25:8000/v1/models # use the container's port NOT the host port
```

## Getting Started
This section describes how to get up-and-running with deployment, assuming that the docker 
swarm networking has already been set up (it has). 

### 1. Get up-to-date repository copies on both hosts
_Before getting started_ make sure to run `git fetch && git pull` from `/home/ubuntu/blacklight/Distributed-Infrastructure` 
on both hosts to ensure that you have up-to-date `docker-compose.yml` files as well as accompaying chat templates, tool 
parsers, et cetera. 

### 2. Set up a .env file 
Some models used in this demo are gated and require a hugging face access token with read permissions (Llama 3.1, Mistral). 
This is referenced in the `docker-compose` files, so you will need to create a `.env` file at `Distributed-Infrastructure/compose/.env`
with the `HUGGINGFACE_TOKEN` variable set. 

_Failure to do this will result in some models failing to start_.

### 3. Run the first compose file on the first host 
_Note: because we are using an overlay network created with docker swarm, you **cannot** use the `docker-compose` command 
since it is not aware of docker swarm._ Instead, you must use the `docker compose` version of the command - both hosts 
have the `compose` plugin for the docker CLI. If you don't have it, get it [here](https://docs.docker.com/compose/install/linux/#install-using-the-repository).

Run the following command on each hostL
```shell
cd /home/ubuntu/blacklight/Distributed-Infrastructure/compose
sudo docker compose -f cluster-1.docker-compose.yml up -d # run in detached mode

# optional: watch the process list to make sure containers start & don't die:
watch -n 2 "docker ps"
```

### 4. Run the second compose file on the second host
Same as above, with the second compose file:

```shell 
cd /home/ubuntu/blacklight/Distributed-Infrastructure/compose
sudo docker compose -f cluster-2.docker-compose.yml up -d 

# optional: watch the container list to make sure containers start without dying
watch -n 2 "docker ps"
```

### 5. Verifying Instance startup &  connectivity 
Since by default the vLLM instances will not be exposed from the host, and are only accessible
through the docker network, you may wish to access them individually to verify that they are 
running successfully, or to verify container connectivity. 

All hosts on the network can be accessed by any other host using the name of the service (e.g. `vllm-0-hermes`) as the hostname. 
The port to use will be the _container_ port (e.g. for vLLM always 8000), not the host port, even if a host port is mapped to the container port.

E.g. the following command would be used to access a vLLM instances from outside the network, if the port `8080` on the host were mapped to port `8000` on the container:
```shell 
curl http://<host IP>:8080/v1/models
```
_Note that by default, vLLM instances **no longer** have exposed ports_. They can only be access through the Docker 
network, and through the LiteLLM proxy.

But from inside the docker network, you would run 
```shell 
curl http://vllm-0-hermes:8000/v1/models # 8000 is the container port used by the vLLM OpenAI image
```

Any container's logs can also be accessed using `sudo docker logs <container name or ID>` e.g. `sudo docker logs vllm-hermes-0`. 

_Note_ that unlike DNS resolution, pulling logs _must_ be done from the host that the container is running on, since even
though we are using docker swarm for networking, we are still using compose for deployment. 

Finally, you can also start a container on the network to verify connectivity:
```shell 
sudo docker run -it --network distributed-inference-secure debian:12-slim

# run inside the container:
apt-get update
apt-get install curl 
apt-get install inetutils-ping
curl http://<service name>:<port>/v1/models
ping <service name>
```

Make sure to stop and remove the container once you are finished with it. Specifying a name with `--name` is _not_ recommended
as this will add the name as a host to the network's DNS, which is fine _until_ you try to create multiple containers with the 
same name (e.g. running the above command more than once, or running it once on each deployment host) at which point 
the networking gets confused and your jumpbox's networking stops working.

### 6. Accessing Models through LiteLLM
[LiteLLM](https://docs.litellm.ai/docs/) provides an OpenAI-compatible proxy that can be connected to a wide variety of 
LLM backends, including non-OpenAI-compatible models. This means you can do neat things like call Anthropic models in an
OpenAI-compatible way!

For our purposes, we're using it to aggregate our vLLM instances into a single endpoint. Right now it's running on port `4000` 
on whichever of the hosts it's started on. Note that you'll need to set the `Authorization` header to use the bearer token, 
like so: `Authorization: Beader sk-...` (ask Kyle for the API key). Once you have done this, you can call any of our 
running vLLM models from that single endpoint using the OpenAI SDK or your toolchain of choice (Vercel AI SDK, anyone?)