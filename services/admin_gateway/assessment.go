package admingateway

import (
	"context"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
)

func (as *AdminGateway) GetAssessment(ctx context.Context, req *connect.Request[v1_messages.GetAssessmentRequest]) (*connect.Response[v1_messages.GetAssessmentResponse], error) {
	return connect.NewResponse(&v1_messages.GetAssessmentResponse{}), nil
}

func (as *AdminGateway) ListAssessments(ctx context.Context, req *connect.Request[v1_messages.ListAssessmentsRequest]) (*connect.Response[v1_messages.ListAssessmentsResponse], error) {
	return connect.NewResponse(&v1_messages.ListAssessmentsResponse{}), nil
}

func (as *AdminGateway) CreateAssessment(ctx context.Context, req *connect.Request[v1_messages.CreateAssessmentRequest]) (*connect.Response[v1_messages.CreateAssessmentResponse], error) {
	return connect.NewResponse(&v1_messages.CreateAssessmentResponse{}), nil
}

func (as *AdminGateway) UpdateAssessment(ctx context.Context, req *connect.Request[v1_messages.UpdateAssessmentRequest]) (*connect.Response[v1_messages.UpdateAssessmentResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateAssessmentResponse{}), nil
}

func (as *AdminGateway) DeleteAssessment(ctx context.Context, req *connect.Request[v1_messages.DeleteAssessmentRequest]) (*connect.Response[v1_messages.DeleteAssessmentResponse], error) {
	return connect.NewResponse(&v1_messages.DeleteAssessmentResponse{}), nil
}
