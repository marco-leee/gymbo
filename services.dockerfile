FROM golang:1.24.4-alpine AS builder

WORKDIR /usr/local/go/src/gymbo.stixman.co

COPY ./services .

RUN mkdir -p /app

RUN go build -o /app/admin_gateway admin_gateway/cmd/server/main.go
RUN go build -o /app/organisation_gateway organisation_gateway/cmd/server/main.go
RUN go build -o /app/trainer_gateway trainer_gateway/cmd/server/main.go
RUN go build -o /app/client_gateway client_gateway/cmd/server/main.go

FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/admin_gateway /app/admin_gateway
COPY --from=builder /app/organisation_gateway /app/organisation_gateway
COPY --from=builder /app/trainer_gateway /app/trainer_gateway
COPY --from=builder /app/client_gateway /app/client_gateway