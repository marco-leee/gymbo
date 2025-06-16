package env

var (
	Env          Environment
	DBConnString string

	StorageEndpoint  string
	StorageAccessKey string
	StorageSecretKey string
	StorageRegion    string
	StorageBucket    string
)

func init() {
	Env = NewEnvironment(GetEnv("ENV", "production"))
	DBConnString = GetEnv("DATABASE_URL", "host=localhost user=admin password=local dbname=gymbo port=32800 sslmode=disable TimeZone=Asia/Hong_Kong")

	StorageEndpoint = GetEnv("STORAGE_ENDPOINT", "http://localhost:9000")
	StorageAccessKey = GetEnv("STORAGE_ACCESS_KEY", "N1NCI6VSTRZZ450BF0L2")
	StorageSecretKey = GetEnv("STORAGE_SECRET_KEY", "ukoME1ySmOOFFqsryykx7GlE5g08L0tdvuBhx6ZC")
	StorageRegion = GetEnv("STORAGE_REGION", "ap-southeast-1")
	StorageBucket = GetEnv("STORAGE_BUCKET", "gymbo")
}
