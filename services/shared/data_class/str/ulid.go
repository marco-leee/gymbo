package str

import (
	"strings"

	"github.com/oklog/ulid/v2"
)

func NewULID() ulid.ULID {
	return ulid.Make()
}

func NewULIDString() string {
	return strings.ToLower(NewULID().String())
}
