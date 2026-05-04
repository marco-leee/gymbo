package main

import clientgateway "gymbo.stixman.co/client_gateway"

func main() {
	server := clientgateway.New()
	server.Serve()
}
