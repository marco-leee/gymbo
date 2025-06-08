package admingateway

import (
	"net/http"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
	"gymbo.stixman.co/admin_gateway/gen/gateways/v1/v1connect"
)

func init() {
}

type AdminGatewayServer struct {
	adminGateway *AdminGateway
}

func newAdminGateway() *AdminGateway {
	return &AdminGateway{}
}

func New() *AdminGatewayServer {
	return &AdminGatewayServer{
		adminGateway: newAdminGateway(),
	}
}

func (ags *AdminGatewayServer) Serve() {
	mux := http.NewServeMux()
	path, handler := v1connect.NewAdminGatewayServiceHandler(ags.adminGateway)
	mux.Handle(path, handler)

	http.ListenAndServe(
		":8080",
		h2c.NewHandler(mux, &http2.Server{}),
	)
}
