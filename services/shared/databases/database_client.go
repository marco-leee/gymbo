package databases

type DatabaseClient struct {
}

type IDatabaseClient interface {
	IsConnected() bool
	Connect() error
	Close() error
	HealthCheck() error
	Migrate(models ...interface{}) error
}
