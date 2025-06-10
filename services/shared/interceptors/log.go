package interceptors

import (
	"context"
	"fmt"

	"connectrpc.com/connect"
)

func LogRequest() connect.UnaryInterceptorFunc {
	interceptor := func(next connect.UnaryFunc) connect.UnaryFunc {
		return connect.UnaryFunc(func(
			ctx context.Context,
			req connect.AnyRequest,
		) (connect.AnyResponse, error) {
			fmt.Printf("[%s] Intercepting %s %s\n", req.Peer().Protocol, req.HTTPMethod(), req.Spec().Procedure)
			return next(ctx, req)
		})
	}
	return connect.UnaryInterceptorFunc(interceptor)
}
