package clientgateway

import (
	"context"

	"connectrpc.com/connect"
	v1 "gymbo.stixman.co/client_gateway/gen/gateways/v1"
	"gymbo.stixman.co/client_gateway/gen/gateways/v1/v1connect"
	entities "gymbo.stixman.co/shared/gen/entities/v1"
)

type ClientGateway struct {
	v1connect.UnimplementedClientGatewayServiceHandler
}

func (cs *ClientGateway) GetClient(ctx context.Context, req *connect.Request[v1.GetClientRequest]) (*connect.Response[v1.GetClientResponse], error) {
	firstName := "John"
	lastName := "Doe"

	return connect.NewResponse(&v1.GetClientResponse{
		Client: &entities.Client{
			Id:        "1",
			FirstName: &firstName,
			LastName:  &lastName,
			Email:     "john.doe@example.com",
		},
	}), nil
}
