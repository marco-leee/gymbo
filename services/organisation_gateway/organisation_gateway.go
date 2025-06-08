package organisationgateway

import (
	"context"

	"connectrpc.com/connect"
	v1 "gymbo.stixman.co/organisation_gateway/gen/gateways/v1"
	"gymbo.stixman.co/organisation_gateway/gen/gateways/v1/v1connect"
)

type OrganisationGateway struct {
	v1connect.UnimplementedOrganisationGatewayServiceHandler
}

func (os *OrganisationGateway) GetOrganisation(ctx context.Context, req *connect.Request[v1.GetOrganisationRequest]) (*connect.Response[v1.GetOrganisationResponse], error) {
	return connect.NewResponse(&v1.GetOrganisationResponse{}), nil
}
