This is a [FastAPI](https://fastapi.tiangolo.com/) project bootstrapped with [Developers Portal](https://developers-portal.weg.net/).

## Getting Started

First, to run in development you may need to create a `.env` file in the root of the project.

This `.env` file should contain the given variables:

|Name|Description|Example|
|-|-|-|
|SWAGGER_SERVERS_LIST|List of servers divided by `,` that are passed to the [servers](https://swagger.io/docs/specification/api-host-and-base-path/) property of OpenAPI|`/,/api`|


run the development server:

```bash
fastapi dev main.py
```

The API will be available at [http://localhost:3000/api](http://localhost:3000/api).

> You can find the docs at [http://localhost:3000/api](http://localhost:3000/api)

## Learn More

To leare more about FastAPI, take a look at the following resources:

- [FastAPI Documentation](https://fastapi.tiangolo.com/learn/) - learn about FastAPI features and API.