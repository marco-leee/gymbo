package database

import (
	"gorm.io/gorm"
	"gymbo.stixman.co/shared/databases"
	"gymbo.stixman.co/shared/env"
)

type AdminGatewayDatabase struct {
	client databases.IPostgresClient
}

func NewAdminGatewayDatabase() *AdminGatewayDatabase {
	postgres := databases.NewPostgres(env.DBConnString)

	if err := postgres.Connect(); err != nil {
		panic(err)
	}

	return &AdminGatewayDatabase{
		client: postgres,
	}
}

func (ad *AdminGatewayDatabase) GetClient() *gorm.DB {
	return ad.client.GetClient()
}
