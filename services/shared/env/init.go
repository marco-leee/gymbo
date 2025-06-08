package env

var (
	Env Environment
)

func init() {
	Env = NewEnvironment(GetEnv("ENV", "production"))
}
