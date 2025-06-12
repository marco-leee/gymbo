package main

import admingateway "gymbo.stixman.co/admin_gateway"

func main() {
	server := admingateway.New()
	server.Serve("8080")
}
