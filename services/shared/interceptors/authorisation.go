package interceptors

import (
	"context"
	"errors"
	"fmt"

	"connectrpc.com/connect"
)

func Authorisation(server string) connect.UnaryInterceptorFunc {
	interceptor := func(next connect.UnaryFunc) connect.UnaryFunc {
		return connect.UnaryFunc(func(
			ctx context.Context,
			req connect.AnyRequest,
		) (connect.AnyResponse, error) {
			fmt.Printf("[%s] TODO: Authorising %s %s\n", req.Peer().Protocol, req.HTTPMethod(), req.Spec().Procedure)

			userRole := req.Header().Get(UserRoleHeader)

			if userRole != server {
				return nil, connect.NewError(connect.CodePermissionDenied, errors.New("unauthorized"))
			}

			// TODO: Check if user is admin in db. use cache

			return next(ctx, req)
		})
	}
	return connect.UnaryInterceptorFunc(interceptor)
}
