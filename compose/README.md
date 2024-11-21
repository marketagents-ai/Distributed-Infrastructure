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


## Getting Started
### 1. Get up-to-date repository copies on both hosts
_Before getting started_ make sure to run `git fetch && git pull` from `/home/ubuntu/blacklight/Distributed-Infrastructure` 
on both hosts to ensure that you have up-to-date `docker-compose.yml` files as well as accompaying chat templates, tool 
parsers, et cetera. 

