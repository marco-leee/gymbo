package database

import (
	"context"

	"gorm.io/gorm"
	"gymbo.stixman.co/shared/databases"
	"gymbo.stixman.co/shared/env"
)

type AdminGatewayDatabase struct {
	client databases.IPostgresClient
}

func New(ctx context.Context) *AdminGatewayDatabase {
	postgres := databases.NewPostgres(ctx, env.DBConnString)

	if err := postgres.Connect(ctx); err != nil {
		panic(err)
	}

	return &AdminGatewayDatabase{
		client: postgres,
	}
}

func (ad *AdminGatewayDatabase) GetClient() *gorm.DB {
	return ad.client.GetClient()
}
