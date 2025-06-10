package interceptors

import (
	"context"
	"fmt"

	"connectrpc.com/connect"
)

func AuthRequest() connect.UnaryInterceptorFunc {
	interceptor := func(next connect.UnaryFunc) connect.UnaryFunc {
		return connect.UnaryFunc(func(
			ctx context.Context,
			req connect.AnyRequest,
		) (connect.AnyResponse, error) {
			token := req.Header().Get("Authorization")
			// if token == "" {
			// 	return nil, connect.NewError(connect.CodeUnauthenticated, errors.New("no token provided"))
			// }

			fmt.Printf("TODO: Authorising request with auth token: %s\n", token)

			return next(ctx, req)
		})
	}
	return connect.UnaryInterceptorFunc(interceptor)
}
