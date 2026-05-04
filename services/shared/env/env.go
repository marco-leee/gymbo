package env

import (
	"log"
	"os"

	"gymbo.stixman.co/shared/data_class/array"
)

type Environment struct {
	value string
}

const (
	development string = "development"
	testing     string = "testing"
	staging     string = "staging"
	production  string = "production"
)

func NewEnvironment(value string) Environment {
	if !array.Contains([]string{development, testing, staging, production}, value) {
		log.Fatalf("Invalid environment: %s", value)
		os.Exit(1)
	}
	return Environment{value: value}
}

func (e Environment) IsDevelopment() bool {
	return e.value == development
}

func (e Environment) IsTesting() bool {
	return e.value == testing
}

func (e Environment) IsStaging() bool {
	return e.value == staging
}

func (e Environment) IsProduction() bool {
	return e.value == production
}
