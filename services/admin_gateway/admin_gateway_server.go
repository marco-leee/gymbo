package admingateway

import (
	"context"
	"fmt"
	"net/http"

	"connectrpc.com/connect"
	"go.uber.org/zap"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
	"gymbo.stixman.co/admin_gateway/database"
	"gymbo.stixman.co/admin_gateway/gen/gateways/v1/v1connect"
	"gymbo.stixman.co/shared/interceptors"
	"gymbo.stixman.co/shared/logger"
	"gymbo.stixman.co/shared/storages"
)

type AdminGateway struct {
	v1connect.UnimplementedAdminGatewayServiceHandler
	db      *database.AdminGatewayDatabase
	storage storages.IObjectStorage
	Logger  *zap.Logger
}

type AdminGatewayServer struct {
	adminGateway *AdminGateway
}

func newAdminGateway(ctx context.Context) *AdminGateway {
	db := database.New(ctx)
	storage, err := storages.NewObjectStorage(ctx)

	if err != nil {
		panic(err)
	}

	return &AdminGateway{
		db:      db,
		storage: storage,
		Logger:  logger.New("admin_gateway"),
	}
}

func New(ctx context.Context) *AdminGatewayServer {
	return &AdminGatewayServer{
		adminGateway: newAdminGateway(ctx),
	}
}

func (ags *AdminGatewayServer) Register(mux *http.ServeMux) {
	path, handler := v1connect.NewAdminGatewayServiceHandler(ags.adminGateway, connect.WithInterceptors(interceptors.LogRequest(), interceptors.Authentication(), interceptors.Authorisation()))
	mux.Handle(path, handler)
}

func (ags *AdminGatewayServer) Serve(port string) {
	mux := http.NewServeMux()
	ags.Register(mux)
	ags.adminGateway.Logger.Info("Starting admin gateway server on port", zap.String("port", port))
	if err := http.ListenAndServe(
		fmt.Sprintf(":%s", port),
		h2c.NewHandler(mux, &http2.Server{}),
	); err != nil {
		ags.adminGateway.Logger.Error("Failed to start admin gateway server", zap.Error(err))
		panic(err)
	}
}
