package main

import (
	"context"

	admingateway "gymbo.stixman.co/admin_gateway"
)

func main() {
	server := admingateway.New(context.Background())
	server.Serve("8080")
}
