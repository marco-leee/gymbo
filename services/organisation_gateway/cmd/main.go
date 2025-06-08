package main

import organisationgateway "gymbo.stixman.co/organisation_gateway"

func main() {
	server := organisationgateway.New()
	server.Serve()
}
