package global_error

import (
	"errors"
	"fmt"

	"connectrpc.com/connect"
	"gymbo.stixman.co/shared/consts"
)

var (
	ErrInvalidFileName       = connect.NewError(connect.CodeInvalidArgument, errors.New("invalid file name"))
	ErrFileSizeLimitExceeded = connect.NewError(connect.CodeInvalidArgument, fmt.Errorf("file size limit exceeded: %d", consts.MAX_FILE_SIZE))
	ErrInvalidFileType       = connect.NewError(connect.CodeInvalidArgument, errors.New("invalid file type"))
)
