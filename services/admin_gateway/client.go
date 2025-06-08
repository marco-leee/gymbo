package admingateway

import (
	"context"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
)

func (as *AdminGateway) GetClient(ctx context.Context, req *connect.Request[v1_messages.GetClientRequest]) (*connect.Response[v1_messages.GetClientResponse], error) {
	return connect.NewResponse(&v1_messages.GetClientResponse{}), nil
}

func (as *AdminGateway) CreateClient(ctx context.Context, req *connect.Request[v1_messages.CreateClientRequest]) (*connect.Response[v1_messages.CreateClientResponse], error) {
	return connect.NewResponse(&v1_messages.CreateClientResponse{}), nil
}

func (as *AdminGateway) UpdateClient(ctx context.Context, req *connect.Request[v1_messages.UpdateClientRequest]) (*connect.Response[v1_messages.UpdateClientResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateClientResponse{}), nil
}

func (as *AdminGateway) DeleteClient(ctx context.Context, req *connect.Request[v1_messages.DeleteClientRequest]) (*connect.Response[v1_messages.DeleteClientResponse], error) {
	return connect.NewResponse(&v1_messages.DeleteClientResponse{}), nil
}

func (as *AdminGateway) ListClients(ctx context.Context, req *connect.Request[v1_messages.ListClientsRequest]) (*connect.Response[v1_messages.ListClientsResponse], error) {
	return connect.NewResponse(&v1_messages.ListClientsResponse{}), nil
}
