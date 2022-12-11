# API: Return the Round Trip Time (RTT), Jitter and Packet Loss to an IP or Hostname

This REST API is containerised with [Docker Compose](https://docs.docker.com/compose/) for a modular and cloud native deployment that fits in any microservice architecture.

Building upon the [FastAPI](https://fastapi.tiangolo.com/) framework that taps into the lightweight and high-performance [Asynchronous Server Gateway Interface](https://asgi.readthedocs.io/en/latest/) (ASGI), [Starlette](https://www.starlette.io/), and the Python data validation module, [Pydantic](https://pydantic-docs.helpmanual.io/); and with the endpoints secured by [Auth0](https://auth0.com/) based on the  JSON Web Key (JWK) specification ([RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517)); it does the following:

1. Validate with Auth0 the JSON Web Token (JWT, [RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)) provided by the client;
2. Ping the given IP address or hostname with the given number of ICMP datagram in an interval of one datagram per second; and
3. Return the round trip time (RTT), jitter and packet loss
    measured.

[NGINX](https://www.nginx.org/) is deployed for the web server, with [Certbot](https://certbot.eff.org/) by the [Electronic Frontier Foundation](https://www.eff.org/) (EFF) for obtaining and renewing a SSL/TLS certificate on a given root domain from [Let’s Encrypt](https://letsencrypt.org/), a non-profit Certificate Authority by the [Internet Security Research Group](https://www.abetterinternet.org/) (ISRG).

A [Bash](https://github.com/gitGNU/gnu_bash) script is imported to execute ping and to convert the output at runtime to comma separated values (CSV), for a subsequent computation with [NumPy](https://github.com/numpy/numpy) and [pandas](https://github.com/matplotlib/matplotlib), of the descriptive statistics on the RTT measured. The source code of the Bash script is available in another [Git repository](#reference).

A detailed walk-through is available [here](https://kurtcms.org/api-return-the-round-trip-time-rtt-jitter-and-packet-loss-to-an-ip-or-hostname/).

## Table of Content

- [Getting Started](#getting-started)
  - [Git Clone](#git-clone)
  - [Auth0 JWT](#auth0-jwt)
  - [Environment Variable](#environment-variables)
  - [Docker Compose](#docker-compose)
	  - [Install](#install)
	  - [SSL/TLS Certificate](#ssltls-certificate)
	  - [Up and Down](#up-and-down)
- [API Specifications](#api-specifications)
	- [GET /pingapi/[ip]?c=[int]](#get-pingapiipcint)
	- [POST /pingapi/](#post-pingapi)
- [SSL/TLS Certificate Renewal](#ssltls-certificate-renewal)
- [Reference](#reference)

## Getting Started

Get started in three simple steps:

1. [Download](#git-clone) a copy of the API;
2. Create the [environment variables](#environment-variables) for retrieving the JSON Web Key Set (JWKS) from Auth0; and
3. [Docker Compose](#docker-compose) to start the API.

### Git Clone

Download a copy of the app with `git clone`
```shell
$ git clone https://github.com/kurtcms/pingapi /app/
```

### Auth0 JWT

A JWT in the OAuth 2.0 Bearer Token schema ([RFC 6750](https://datatracker.ietf.org/doc/html/rfc6750)) is required to access the API.

[Register](https://auth0.com/docs/get-started/auth0-overview/set-up-apis) an API with Auth0, and then retrieve an access token with the domain, the client ID, the client secret and the audience of the registered API.

```shell
$ curl --request POST \
    --url https://kurtcms.us.auth0.com/oauth/token \
    --header "content-type: application/json" \
    --data '{"client_id":"(redacted)","client_secret":"(redacted),"audience":"https://kurtcms.com/pingapi/","grant_type":"client_credentials"}'
```

### Environment Variables

The API expects the domain, the issuer, the audience and the signing algorithm for retrieving the JWKS from Auth0, as environment variables in a `.env` file in the same directory.

Be sure to create the `.env` file.

```shell
$ nano /app/pingapi/.env
```

And define the variables accordingly.

```
# For retrieving the JSON Web Key Set (JWKS) from Auth0
AUTH0_DOMAIN = kurtcms.us.auth0.com
AUTH0_ISSUER = https://kurtcms.us.auth0.com/
AUTH0_AUDIENCE = https://kurtcms.com/pingapi/
AUTH0_ALGORITHMS = RS256
```

### Docker Compose

With Docker Compose, the API may be provisioned with a single command.

#### Install

Install [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) with the Bash script that comes with API.

```shell
$ chmod +x /app/pingapi/install-docker-compose \
    && /app/pingapi/install-docker-compose
```

#### SSL/TLS Certificate

A dummy SSL/TLS certificate and private key will need to be created for NGINX to start service, and for Certbot to subsequently obtain a signed SSL/TLS certificate from Let’s Encrypt by answering a [HTTP-01 challenge](https://letsencrypt.org/docs/challenge-types/#http-01-challenge).

Create the dummy certificate before obtaining a signed one with the Bash script that comes with API.

```shell
$ chmod +x /app/pingapi/fetch-certbot-tls \
    && /app/pingapi/fetch-certbot-tls
```

Enter the root domain and the email address for registration and recovery when prompted.

#### Up and Down

Start the containers with Docker Compose.

```shell
$ docker-compose up -d
```

Stopping the containers is as simple as a single command.

```shell
$ docker-compose down
```

## API Specifications

Powered by [Swagger UI](https://github.com/swagger-api/swagger-ui), an OpenAPI, or formerly known as Swagger, specification is available at /docs. An alternative specification powered by [Redoc](https://github.com/Redocly/redoc) is also available at /redoc.

Below are the endpoints available along with their corresponding parameters and responses.

### GET /pingapi/[ip]?c=[int]

Return the RTT, jitter and packet loss to the given IP address or hostname in the specified duration as measured by ping at one ICMP datagram per second.

Duration must be greater than 0 and less than 60.

```shell
$ curl -X GET https://kurtcms.com/pingapi/1.1.1.1?c=5 \
    -H "Authorization: Bearer (redacted)" \
    -i
```

#### Response

```
HTTP/1.1 200 OK
date: Thu, 24 Feb 2022 15:45:30 GMT
server: uvicorn
content-length: 167
content-type: application/json

{"date_time":"20220224154530","ip_host":"1.1.1.1","rtt_mean":2.56,"rtt_min":2.17,"rtt_max":3.62,"jitter":0.61,"count_requested":5,"count_received":5,"packet_loss":0.0}
```

### POST /pingapi

Return the RTT, jitter and packet loss to the given IP address or hostname in the specified duration as measured by ping at one ICMP datagram per second.

Duration must be greater than 0 and less than 60.

```shell
$ curl -X POST https://kurtcms.com/pingapi/ \
    -H "Authorization: Bearer (redacted)" \
    -H "Content-Type: application/json" \
    -d '{"ip":"1.1.1.1","c":"5"}' \
    -i
```

#### Response

```
HTTP/1.1 200 OK
date: Thu, 24 Feb 2022 15:45:45 GMT
server: uvicorn
content-length: 167
content-type: application/json

{"date_time":"20220224154545","ip_host":"1.1.1.1","rtt_mean":2.61,"rtt_min":2.13,"rtt_max":3.82,"jitter":0.71,"count_requested":5,"count_received":5,"packet_loss":0.0}
```

## SSL/TLS Certificate Renewal

Certbot is instructed by Docker Compose to attempt a SSL/TLS certificate renewal every 12 hours, which should be more than adequate considering the certificate is [valid for 90 days](https://letsencrypt.org/docs/faq/#what-is-the-lifetime-for-let-s-encrypt-certificates-for-how-long-are-they-valid).

NGINX is instructed to reload its configuration every 24 hours to ensure the renewed certificate will come into effect at most 12 hours after a renewal, which should also be well in advance of an impending expiry.

Edit the `docker-compose.yml` should these intervals need to be adjusted.

```shell
$ nano /app/pingapi/docker-compose.yml
```

Modify the values as appropriate.

```
  nginx:
    ...
    command: "/bin/sh -c 'while :; do sleep 24h & wait $${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  certbot:
    ...
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

## Reference

- [IP Networking: Ping Output to Comma Separated Values (CSV) at Runtime](https://github.com/kurtcms/pingc)