# WebSocket API

This file contains details about the WebSocket API that the web server provides.

After a successful login or signup, clients should connect to the `/ws` endpoint of the web server. The connection request should carry a `session_token` cookie. A missing or invalid `session_token` cookie will result in a 401 Unauthorized response code (the initial HTTP connection will not be upgraded to a WebSocket connection).

Every WebSocket message (sent either by the client or the server) represents a data update operation. For example, a client could send the server a message informing the server that the client has removed a certain product from the inventory list. Upon receiving this message, the server would apply the corresponding changes to the database, then it would send the same message to other clients in the kitchen to inform them of the change. Once the other clients receive the message, they would update their UI to reflect the change.

All WebSocket messages will have the following fields in JSON.

| Field         | Description                                                  |
| ------------- | ------------------------------------------------------------ |
| kitchen_id    | A string containing the ID of the kitchen to be updated.     |
| update_target | A string specifying the aspect of the kitchen to be updated. This can be  `"kitchen"` to modify data about the kitchen itself, `"grocery"` to modify a grocery item, `"inventory"` to modify an inventory item, and `"custom"` to modify a custom product. |
| action        | A string specifying the type of update to be performed on the update target. The possible values of this field are dependent on the update target. |
| data          | An object containing the updated data. The format of this object is dependent on the update target and action. |

Here's an example of a message:

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "grocery",
    "action": "add",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "amount": 1
    }
}
```

Our WebSocket API has been designed to allow messages to be "forwardable": when a client sends the server a message about a data update, the server applies the corresponding changes to the database, then sends that same message to all the other relevant clients (i.e. the clients in the same kitchen). In a sense, messages can be "forwarded" from one client to many others.

**Update targets and actions**

- [Kitchen](#kitchen)
  - [Create](#create)
  - [Rename](#rename)
  - [Share](#share)
  - [Delete](#delete)

- [Grocery](#grocery)
  - [Add](#add)
  - [Remove](#remove)

- [Inventory](#inventory)
  - [Add](#add-1)
  - [Remove](#remove-1)

- [Custom](#custom)
  - [Create](#create-1)
  - [Rename](#rename-1)
  - [Update image](#update-image)
  - [Update barcodes](#update-barcodes)
  - [Delete](#delete-1)


## Kitchen

The `kitchen` update target indicates a modification of data about the kitchen itself.

### Create

The `create` action creates a new kitchen.

> This message is only sent by the server, not the client.

#### Data object format

| Field | Description                                  |
| ----- | -------------------------------------------- |
| name  | A string containing the name of the kitchen. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "kitchen",
    "action": "create",
    "data": {
        "name": "Home kitchen"
    }
}
```

### Rename

The `rename` action changes the name of a kitchen.

#### Data object format

| Field | Description                                      |
| ----- | ------------------------------------------------ |
| name  | A string containing the new name of the kitchen. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "kitchen",
    "action": "rename",
    "data": {
        "name": "Home kitchen"
    }
}
```

### Share

The `share` action allows other users access to the kitchen.

#### Data object format

| Field      | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| share_with | An array of strings containing user emails with which to share the kitchen. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "kitchen",
    "action": "share",
    "data": {
        "share_with": [
            "aaron@gmail.com",
            "sally@gmail.com"
        ]
    }
}
```

### Delete

The `delete` action deletes a kitchen.

#### Data object format

This message carries an empty data object.

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "kitchen",
    "action": "delete",
    "data": {}
}
```

## Grocery

The `grocery` update target indicates a modification of data about an item in the grocery list.

### Add

The `add` action adds an item to the grocery list.

#### Data object format

| Field      | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| product_id | A string containing the ID of the product being added to the grocery list. This can either be a default product or a custom product. |
| amount     | An integer specifying the amount of the product to add to the grocery list. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "grocery",
    "action": "add",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "amount": 1
    }
}
```

### Remove

The `remove` action removes an item from the grocery list.

#### Data object format

| Field      | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| product_id | A string containing the ID of the product being removed from the grocery list. This can either be a default product or a custom product. |
| amount     | An integer specifying the amount of the product to remove from the grocery list. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "grocery",
    "action": "remove",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "amount": 1
    }
}
```

## Inventory

The `inventory` update target indicates a modification of data about an item in the inventory list.

### Add

The `add` action adds an item to the inventory list.

#### Data object format

| Field      | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| product_id | A string containing the ID of the product being added to the inventory list. This can either be a default product or a custom product. |
| amount     | An integer specifying the amount of the product to add to the inventory list. |
| expiry     | An integer specifying the expiry date of the item, in Unix timestamp format. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "inventory",
    "action": "add",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "amount": 1,
        "expiry": 1670256000
    }
}
```

### Remove

The `remove` action removes an item from the inventory list.

#### Data object format

| Field      | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| product_id | A string containing the ID of the product being removed from the inventory list. This can either be a default product or a custom product. |
| amount     | An integer specifying the amount of the product to remove from the inventory list. |
| expiry     | An integer specifying the expiry date of the item, in Unix timestamp format. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "inventory",
    "action": "remove",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "amount": 1,
        "expiry": 1670256000
    }
}
```

## Custom

The `custom` update target indicates a modification of data about a custom product.

### Create

The `create` action creates a custom product.

> This message is only sent by the server, not the client.

#### Data object format

| Field      | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| product_id | A string containing the ID of the new product.               |
| name       | A string containing the name of the new product.             |
| barcodes   | An array of integers specifying the barcodes that the new product has (a product can have more than one barcode). |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "custom",
    "action": "create",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "name": "Ripe Red Tomatoes",
        "barcodes": [
            8887419109224
        ]
    }
}
```

### Rename

The `rename` action changes the name of a custom product.

#### Data object format

| Field      | Description                                             |
| ---------- | ------------------------------------------------------- |
| product_id | A string containing the ID of the custom product.       |
| name       | A string containing the new name of the custom product. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "custom",
    "action": "rename",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "name": "Round Orange Oranges"
    }
}
```

### Update image

The `update_image` action notifies clients that the image of a custom product has been updated. This message doesn't modify the actual image data itself; that is instead done via a HTTP POST request to `/x-image/{kid}/{pid}`. The API is designed this way to limit WebSocket messages to JSON, for standardisation purposes. All binary (image) data is hence transferred through HTTP.

> This message is only sent by the server, not the client.

#### Data object format

| Field      | Description                                       |
| ---------- | ------------------------------------------------- |
| product_id | A string containing the ID of the custom product. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "custom",
    "action": "update_image",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi"
    }
}
```

### Update barcodes

The `update_barcodes` action changes the barcodes of a custom product.

#### Data object format

| Field      | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| product_id | A string containing the ID of the custom product.            |
| barcodes   | An array of integers specifying the barcodes that the custom product has (a product can have more than one barcode). |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "custom",
    "action": "update_barcodes",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi",
        "barcodes": [
            8887419109095
        ]
    }
}
```

### Delete

The `delete` message deletes a custom product from a kitchen.

#### Data object format

| Field      | Description                                       |
| ---------- | ------------------------------------------------- |
| product_id | A string containing the ID of the custom product. |

#### Message example

```json
{
    "kitchen_id": "GRHS6JPKv3Iixoo5P5CB",
    "update_target": "custom",
    "action": "delete",
    "data": {
        "product_id": "NFIJaFyE6lJhOgicIjCi"
    }
}
```
