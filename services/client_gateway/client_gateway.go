package clientgateway

import (
	"context"
	"fmt"

	"connectrpc.com/connect"
	v1 "gymbo.stixman.co/client_gateway/gen/gateways/v1"
	"gymbo.stixman.co/client_gateway/gen/gateways/v1/v1connect"
	entities "gymbo.stixman.co/shared/gen/entities/v1"
	"gymbo.stixman.co/shared/models"
)

type ClientGateway struct {
	v1connect.UnimplementedClientGatewayServiceHandler
}

func (cs *ClientGateway) GetClient(ctx context.Context, req *connect.Request[v1.GetClientRequest]) (*connect.Response[v1.GetClientResponse], error) {
	client := models.Client{}
	fmt.Println("h", client)
	return connect.NewResponse(&v1.GetClientResponse{
		Client: &entities.Client{
			Id:        "1",
			FirstName: "John",
			LastName:  "Doe",
			Email:     "john.doe@example.com",
		},
	}), nil
}
