package databases

import "context"

type DatabaseClient struct {
}

type IDatabaseClient interface {
	IsConnected() bool
	Connect(ctx context.Context) error
	Close() error
	HealthCheck() error
	Migrate(models ...interface{}) error
}
