package env

var (
	Env          Environment
	DBConnString string
)

func init() {
	Env = NewEnvironment(GetEnv("ENV", "production"))
	DBConnString = GetEnv("DATABASE_URL", "host=localhost user=admin password=local dbname=gymbo port=32800 sslmode=disable TimeZone=Asia/Hong_Kong")
}
