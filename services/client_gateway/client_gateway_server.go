package clientgateway

import (
	"net/http"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
	"gymbo.stixman.co/client_gateway/gen/gateways/v1/v1connect"
)

func init() {
}

type ClientGatewayServer struct {
	clientGateway *ClientGateway
}

func newClientGateway() *ClientGateway {
	return &ClientGateway{}
}

func New() *ClientGatewayServer {
	return &ClientGatewayServer{
		clientGateway: newClientGateway(),
	}
}

func (cgs *ClientGatewayServer) Serve() {
	mux := http.NewServeMux()
	path, handler := v1connect.NewClientGatewayServiceHandler(cgs.clientGateway)
	mux.Handle(path, handler)

	http.ListenAndServe(
		":8080",
		h2c.NewHandler(mux, &http2.Server{}),
	)
}
