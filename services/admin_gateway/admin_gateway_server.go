package admingateway

import (
	"net/http"

	"connectrpc.com/connect"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
	"gymbo.stixman.co/admin_gateway/gen/gateways/v1/v1connect"
	"gymbo.stixman.co/shared/interceptors"
)

func init() {
}

type AdminGateway struct {
	v1connect.UnimplementedAdminGatewayServiceHandler
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

func (ags *AdminGatewayServer) Register(mux *http.ServeMux) {
	path, handler := v1connect.NewAdminGatewayServiceHandler(ags.adminGateway, connect.WithInterceptors(interceptors.LogRequest()))
	mux.Handle(path, handler)
}

func (ags *AdminGatewayServer) Serve() {
	mux := http.NewServeMux()
	ags.Register(mux)
	http.ListenAndServe(
		":8080",
		h2c.NewHandler(mux, &http2.Server{}),
	)
}
