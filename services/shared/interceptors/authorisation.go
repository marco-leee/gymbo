package interceptors

import (
	"context"
	"fmt"

	"connectrpc.com/connect"
)

func Authorisation() connect.UnaryInterceptorFunc {
	interceptor := func(next connect.UnaryFunc) connect.UnaryFunc {
		return connect.UnaryFunc(func(
			ctx context.Context,
			req connect.AnyRequest,
		) (connect.AnyResponse, error) {
			token := req.Header().Get("Authorization")
			// if token == "" {
			// 	return nil, connect.NewError(connect.CodeUnauthenticated, errors.New("no token provided"))
			// }
			fmt.Printf("[%s] TODO: Authorising %s %s: token %s\n", req.Peer().Protocol, req.HTTPMethod(), req.Spec().Procedure, token)

			return next(ctx, req)
		})
	}
	return connect.UnaryInterceptorFunc(interceptor)
}
