# API requirements

## Services

### Client Service

### Trainer Service

### Organisation Service



> Organised by pages

- All paths with prefix `/api/v1`

## Base Response

```json
{
  "status": "success" | "error",
  "error": {
      "code": 0,
      "type": "",
      "message": ""
  },
  "data": {}
}
```

## Index

| Path | Description | Method | Params |
| --- | --- | --- | --- |
| `/auth/login` | Login | POST | `email`, `password` |
| `/auth/register` | Register (Not exposed) | POST | `email`, `password` |


```json
{
   "token": "token"
}
```

## Exercises

| Path | Description | Method | Query String | 
| --- | --- | --- | --- |
| `/exercises` | Get all exercises | GET | `start_from`, `end_at` |
| `/exercises/:id` | Get exercise by id | GET |  |
| `/exercises` | Create exercise | POST |  |
| `/exercises/:id` | Update exercise | PUT |  |
| `/media/sign` | Sign upload to bucket | POST |  |

```json
{

}
```

## Clients

| Path | Description | Method | Params |
| --- | --- | --- | --- |
| `/clients` | Get all clients | GET |  |
| `/clients/:id` | Get client by id | GET |  |
| `/clients` | Create client | POST |  |
| `/clients/:id` | Update client | PUT |  |


## Trainers

| Path | Description | Method | Params |
| --- | --- | --- | --- |
| `/trainers` | Get all trainers | GET |  |
| `/trainers/:id` | Get trainer by id | GET |  |
| `/trainers` | Create trainer | POST |  |
| `/trainers/:id` | Update trainer | PUT |  |