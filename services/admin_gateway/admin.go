package admingateway

import (
	"context"

	"connectrpc.com/connect"
	v1 "gymbo.stixman.co/admin_gateway/gen/gateways/v1"
)

func (as *AdminGateway) GetAdmin(ctx context.Context, req *connect.Request[v1.GetAdminRequest]) (*connect.Response[v1.GetAdminResponse], error) {
	return connect.NewResponse(&v1.GetAdminResponse{}), nil
}

func (as *AdminGateway) RegisterAdmin(ctx context.Context, req *connect.Request[v1.RegisterAdminRequest]) (*connect.Response[v1.RegisterAdminResponse], error) {
	return connect.NewResponse(&v1.RegisterAdminResponse{}), nil
}
