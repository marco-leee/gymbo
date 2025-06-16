package global_error

import (
	"connectrpc.com/connect"
	"google.golang.org/genproto/googleapis/rpc/errdetails"
)

func AddDetails(err *connect.Error, domain string, reason string) *connect.Error {
	info := &errdetails.ErrorInfo{
		Reason: reason,
		Domain: domain,
	}

	if detail, detailErr := connect.NewErrorDetail(info); detailErr == nil {
		err.AddDetail(detail)
	}

	return err
}
