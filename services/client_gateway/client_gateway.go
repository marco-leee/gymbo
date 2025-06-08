package clientgateway

import (
	"context"
	"fmt"

	"connectrpc.com/connect"
	v1 "gymbo.stixman.co/client_gateway/gen/gateways/v1"
	"gymbo.stixman.co/client_gateway/gen/gateways/v1/v1connect"
	"gymbo.stixman.co/shared/models"
)

type ClientGateway struct {
	v1connect.UnimplementedClientGatewayServiceHandler
}

func (cs *ClientGateway) GetClient(ctx context.Context, req *connect.Request[v1.GetClientRequest]) (*connect.Response[v1.GetClientResponse], error) {
	client := models.Client{}
	fmt.Println("h", client)
	return connect.NewResponse(&v1.GetClientResponse{}), nil
}
