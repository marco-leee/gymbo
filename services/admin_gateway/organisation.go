package admingateway

import (
	"context"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
)

func (as *AdminGateway) GetOrganisation(ctx context.Context, req *connect.Request[v1_messages.GetOrganisationRequest]) (*connect.Response[v1_messages.GetOrganisationResponse], error) {
	return connect.NewResponse(&v1_messages.GetOrganisationResponse{}), nil
}

func (as *AdminGateway) CreateOrganisation(ctx context.Context, req *connect.Request[v1_messages.CreateOrganisationRequest]) (*connect.Response[v1_messages.CreateOrganisationResponse], error) {
	return connect.NewResponse(&v1_messages.CreateOrganisationResponse{}), nil
}

func (as *AdminGateway) UpdateOrganisation(ctx context.Context, req *connect.Request[v1_messages.UpdateOrganisationRequest]) (*connect.Response[v1_messages.UpdateOrganisationResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateOrganisationResponse{}), nil
}

func (as *AdminGateway) DeleteOrganisation(ctx context.Context, req *connect.Request[v1_messages.DeleteOrganisationRequest]) (*connect.Response[v1_messages.DeleteOrganisationResponse], error) {
	return connect.NewResponse(&v1_messages.DeleteOrganisationResponse{}), nil
}

func (as *AdminGateway) ListOrganisations(ctx context.Context, req *connect.Request[v1_messages.ListOrganisationRequest]) (*connect.Response[v1_messages.ListOrganisationResponse], error) {
	return connect.NewResponse(&v1_messages.ListOrganisationResponse{}), nil
}
