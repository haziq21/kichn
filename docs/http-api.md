# HTTP API

This file contains specifications about the HTTP API that the web server provides. All request and response bodies are in JSON format, unless otherwise specified to be binary image data.

**Table of contents**

- [POST /login](#post-login)
- [POST /signup](#post-signup)
- [GET /product/{pid}](#get-productpid)
- [GET /image/{pid}](#get-imagepid)
- [GET /x-image/{kid}/{pid}](#get-x-imagekidpid)
- [POST /x-image/{kid}/{pid}](#post-x-imagekidpid)
- [PUT /x-image/{kid}/{pid}](#put-x-imagekidpid)

## POST /login

Allows a user to access their account.

### Request body format

| Field    | Value                                            |
| -------- | ------------------------------------------------ |
| email    | A string containing the user's email address.    |
| password | A string containing the user's account password. |

### Request body example

```json
{
    "email": "john@gmail.com",
    "password": "correct horse battery staple"
}
```

### Possible response codes

| Status code      | Explanation                                                  |
| ---------------- | ------------------------------------------------------------ |
| 200 OK           | The login was successful. This response also sets a `session_token` cookie (via the `set-cookie` header) containing the user's session token. |
| 400 Bad Request  | The request body did not include the expected fields.        |
| 401 Unauthorized | The login credentials are invalid - either the email address does not exist in the database, or the password is incorrect. |

## POST /signup

Allows a user to create an account.

### Request body format

| Field    | Value                                            |
| -------- | ------------------------------------------------ |
| name     | A string containing the user's name.             |
| email    | A string containing the user's email address.    |
| password | A string containing the user's account password. |

### Request body example

```json
{
    "name": "John Doe",
    "email": "john@gmail.com",
    "password": "correct horse battery staple"
}
```

### Possible response codes

| Status code     | Explanation                                                  |
| --------------- | ------------------------------------------------------------ |
| 200 OK          | The login was successful. This response also sets a `session_token` cookie (via the `set-cookie` header) containing the user's session token. |
| 400 Bad Request | The request body did not include the expected fields.        |
| 409 Conflict    | The email address already exists in the database (i.e. the user already has an account). |

## GET /product/{pid}

Returns information about a default product, where `{pid}` is the ID of the product.

### Possible response codes

| Status code   | Explanation                                                  |
| ------------- | ------------------------------------------------------------ |
| 200 OK        | The specified product exists. This response will also include a body. |
| 404 Not Found | The specified product does not exist.                        |

### Response body format

| Field    | Value                                                        |
| -------- | ------------------------------------------------------------ |
| name     | A string containing the name of the product.                 |
| category | A string containing the product category that the product is in. |
| barcodes | An array of integers containing barcodes that the product has (one product can have multiple barcodes). |

### Response body example

```json
{
    "name": "Kellogg's Cereal - Cornflakes (Jumbo Pack)",
    "category": "Breakfast",
    "barcodes": [8852756346053]
}
```

## GET /image/{pid}

Returns the image of a default product, where `{pid}` is the ID of the product.

### Possible response codes

| Status code   | Explanation                                                  |
| ------------- | ------------------------------------------------------------ |
| 200 OK        | The specified product exists. This response will also include a body. |
| 404 Not Found | The specified product does not exist.                        |

### Response body format

The response body will contain binary image data.

## GET /x-image/{kid}/{pid}

Returns the image of a custom product, where `{kid}` is the ID of the kitchen that the custom product is from, and  `{pid}` is the ID of the product.

### Possible response codes

| Status code   | Explanation                                                  |
| ------------- | ------------------------------------------------------------ |
| 200 OK        | The specified product exists. This response will also include a body. |
| 403 Forbidden | The user does not have access to the kitchen that the custom product is from. The user's identity is determined from the `session_token` cookie sent with the request. |
| 404 Not Found | The specified product does not exist.                        |

### Response body format

The response body will contain binary image data.

## POST /x-image/{kid}/{pid}

Sets the image of a custom product, where `{kid}` is the ID of the kitchen that the custom product is from, and `{pid}` is the ID of the product.

### Request body format

The request body should contain binary image data.

### Possible response codes

| Status code   | Explanation                                                  |
| ------------- | ------------------------------------------------------------ |
| 200 OK        | The image was successfully set.                              |
| 403 Forbidden | The user does not have access to the kitchen that the custom product is from. The user's identity is determined from the `session_token` cookie sent with the request. |
| 409 Conflict  | The specified product already has an image.                  |

## PUT /x-image/{kid}/{pid}

Updates the image of a custom product, where `{kid}` is the ID of the kitchen that the custom product is from, and `{pid}` is the ID of the product.

### Request body format

The request body should contain binary image data.

### Possible response codes

| Status code   | Explanation                                                  |
| ------------- | ------------------------------------------------------------ |
| 200 OK        | The image was successfully updated.                          |
| 403 Forbidden | The user does not have access to the kitchen that the custom product is from. The user's identity is determined from the `session_token` cookie sent with the request. |
