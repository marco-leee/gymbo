package global_error

import (
	"errors"

	"connectrpc.com/connect"
)

var (
	ErrFieldRequired = connect.NewError(connect.CodeInvalidArgument, errors.New("field is required"))
)
