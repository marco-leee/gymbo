package global_error

import (
	"errors"

	"connectrpc.com/connect"
)

var (
	ErrDatabaseConnectionFailed = connect.NewError(connect.CodeInternal, errors.New("database connection failed"))
	ErrDatabaseMigrationFailed  = connect.NewError(connect.CodeInternal, errors.New("database migration failed"))

	ErrEmailAlreadyInUse = connect.NewError(connect.CodeAlreadyExists, errors.New("email already in use"))
	ErrEmailRequired     = connect.NewError(connect.CodeInvalidArgument, errors.New("email is required"))

	ErrEntityNotFound = connect.NewError(connect.CodeNotFound, errors.New("entity not found"))
)
