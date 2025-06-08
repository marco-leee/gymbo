package admingateway

import (
	"context"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
)

func (as *AdminGateway) GetTrainer(ctx context.Context, req *connect.Request[v1_messages.GetTrainerRequest]) (*connect.Response[v1_messages.GetTrainerResponse], error) {
	return connect.NewResponse(&v1_messages.GetTrainerResponse{}), nil
}

func (as *AdminGateway) ListTrainers(ctx context.Context, req *connect.Request[v1_messages.ListTrainersRequest]) (*connect.Response[v1_messages.ListTrainersResponse], error) {
	return connect.NewResponse(&v1_messages.ListTrainersResponse{}), nil
}

func (as *AdminGateway) CreateTrainer(ctx context.Context, req *connect.Request[v1_messages.CreateTrainerRequest]) (*connect.Response[v1_messages.CreateTrainerResponse], error) {
	return connect.NewResponse(&v1_messages.CreateTrainerResponse{}), nil
}

func (as *AdminGateway) UpdateTrainer(ctx context.Context, req *connect.Request[v1_messages.UpdateTrainerRequest]) (*connect.Response[v1_messages.UpdateTrainerResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateTrainerResponse{}), nil
}

func (as *AdminGateway) DeleteTrainer(ctx context.Context, req *connect.Request[v1_messages.DeleteTrainerRequest]) (*connect.Response[v1_messages.DeleteTrainerResponse], error) {
	return connect.NewResponse(&v1_messages.DeleteTrainerResponse{}), nil
}
