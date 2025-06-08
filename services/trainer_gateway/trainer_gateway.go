package trainergateway

import (
	"context"

	"connectrpc.com/connect"
	v1 "gymbo.stixman.co/trainer_gateway/gen/gateways/v1"
	"gymbo.stixman.co/trainer_gateway/gen/gateways/v1/v1connect"
)

type TrainerGateway struct {
	v1connect.UnimplementedTrainerGatewayServiceHandler
}

func (ts *TrainerGateway) GetUser(ctx context.Context, req *connect.Request[v1.GetUserRequest]) (*connect.Response[v1.GetUserResponse], error) {
	return connect.NewResponse(&v1.GetUserResponse{}), nil
}
