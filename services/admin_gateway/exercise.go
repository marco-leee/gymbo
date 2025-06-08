package admingateway

import (
	"context"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
)

func (as *AdminGateway) GetExercise(ctx context.Context, req *connect.Request[v1_messages.GetExerciseRequest]) (*connect.Response[v1_messages.GetExerciseResponse], error) {
	return connect.NewResponse(&v1_messages.GetExerciseResponse{}), nil
}

func (as *AdminGateway) ListExercises(ctx context.Context, req *connect.Request[v1_messages.ListExercisesRequest]) (*connect.Response[v1_messages.ListExercisesResponse], error) {
	return connect.NewResponse(&v1_messages.ListExercisesResponse{}), nil
}

func (as *AdminGateway) CreateExercise(ctx context.Context, req *connect.Request[v1_messages.CreateExerciseRequest]) (*connect.Response[v1_messages.CreateExerciseResponse], error) {
	return connect.NewResponse(&v1_messages.CreateExerciseResponse{}), nil
}

func (as *AdminGateway) UpdateExercise(ctx context.Context, req *connect.Request[v1_messages.UpdateExerciseRequest]) (*connect.Response[v1_messages.UpdateExerciseResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateExerciseResponse{}), nil
}

func (as *AdminGateway) DeleteExercise(ctx context.Context, req *connect.Request[v1_messages.DeleteExerciseRequest]) (*connect.Response[v1_messages.DeleteExerciseResponse], error) {
	return connect.NewResponse(&v1_messages.DeleteExerciseResponse{}), nil
}
