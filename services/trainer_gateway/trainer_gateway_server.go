package trainergateway

import (
	"net/http"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
	"gymbo.stixman.co/trainer_gateway/gen/gateways/v1/v1connect"
)

func init() {
}

type TrainerGatewayServer struct {
	trainerGateway *TrainerGateway
}

func newTrainerGateway() *TrainerGateway {
	return &TrainerGateway{}
}

func New() *TrainerGatewayServer {
	return &TrainerGatewayServer{
		trainerGateway: newTrainerGateway(),
	}
}

func (tgs *TrainerGatewayServer) Serve() {
	mux := http.NewServeMux()
	path, handler := v1connect.NewTrainerGatewayServiceHandler(tgs.trainerGateway)
	mux.Handle(path, handler)

	http.ListenAndServe(
		":8080",
		h2c.NewHandler(mux, &http2.Server{}),
	)
}
