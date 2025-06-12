package databases

import (
	"database/sql"
	"sync"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/schema"
)

type PostgresClient struct {
	DatabaseClient
	once       sync.Once
	connString string
	db         *sql.DB
	client     *gorm.DB
}

type IPostgresClient interface {
	IDatabaseClient
	GetClient() *gorm.DB
}

func NewPostgres(connString string) IPostgresClient {
	return &PostgresClient{
		connString: connString,
	}
}

func (p *PostgresClient) GetClient() *gorm.DB {
	return p.client
}

func (p *PostgresClient) Migrate(models ...interface{}) error {
	return p.client.AutoMigrate(models...)
}

func (p *PostgresClient) Close() error {
	return p.db.Close()
}

func (p *PostgresClient) Connect() error {
	var err error

	p.once.Do(func() {
		p.client, err = gorm.Open(postgres.Open(p.connString), &gorm.Config{
			NamingStrategy: schema.NamingStrategy{
				SingularTable: true,
				NoLowerCase:   false,
			},
		})

		if err != nil {
			return
		}

		sqlDB, err := p.client.DB()

		if err != nil {
			return
		}

		sqlDB.SetMaxIdleConns(10)
		sqlDB.SetMaxOpenConns(100)
		sqlDB.SetConnMaxLifetime(time.Hour)

		p.db = sqlDB
	})

	return err
}

func (p *PostgresClient) IsConnected() bool {
	return p.HealthCheck() == nil
}

func (p *PostgresClient) HealthCheck() error {
	db, err := p.client.DB()

	if err != nil {
		return err
	}

	return db.Ping()
}
