package organisationgateway

import (
	"net/http"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
	"gymbo.stixman.co/organisation_gateway/gen/gateways/v1/v1connect"
)

func init() {
}

type OrganisationGatewayServer struct {
	organisationGateway *OrganisationGateway
}

func newOrganisationGateway() *OrganisationGateway {
	return &OrganisationGateway{}
}

func New() *OrganisationGatewayServer {
	return &OrganisationGatewayServer{
		organisationGateway: newOrganisationGateway(),
	}
}

func (ogs *OrganisationGatewayServer) Serve() {
	mux := http.NewServeMux()
	path, handler := v1connect.NewOrganisationGatewayServiceHandler(ogs.organisationGateway)
	mux.Handle(path, handler)

	http.ListenAndServe(
		":8080",
		h2c.NewHandler(mux, &http2.Server{}),
	)
}
