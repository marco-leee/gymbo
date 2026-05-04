package interceptors

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"connectrpc.com/connect"
	"gymbo.stixman.co/shared/crypto"
	"gymbo.stixman.co/shared/data_class/array"
)

const (
	UserIdHeader    = "x-user-id"
	UserRoleHeader  = "x-user-role"
	UserEmailHeader = "x-user-email"
)

var skipRoutes = []string{
	"/gateways.admin.v1.AdminGatewayService/Login",
	"/gateways.admin.v1.AdminGatewayService/RefreshToken",
}

func Authentication(tokenManager crypto.ITokenManager) connect.UnaryInterceptorFunc {
	interceptor := func(next connect.UnaryFunc) connect.UnaryFunc {
		return connect.UnaryFunc(func(
			ctx context.Context,
			req connect.AnyRequest,
		) (connect.AnyResponse, error) {
			if array.Contains(skipRoutes, req.Spec().Procedure) {
				return next(ctx, req)
			}

			fmt.Printf("[%s] Authenticating %s %s\n", req.Peer().Protocol, req.HTTPMethod(), req.Spec().Procedure)

			token := req.Header().Get("Authorization")

			if token == "" {
				return nil, connect.NewError(connect.CodeUnauthenticated, errors.New("missing token"))
			}

			token = strings.TrimPrefix(token, "Bearer ")

			if err := tokenManager.VerifyToken(token); err != nil {
				return nil, connect.NewError(connect.CodeUnauthenticated, fmt.Errorf("invalid token: %w", err))
			}

			claims, err := tokenManager.GetPayload(token)

			if err != nil {
				return nil, connect.NewError(connect.CodeUnauthenticated, fmt.Errorf("invalid payload: %w", err))
			}

			req.Header().Set(UserIdHeader, claims.Id)
			req.Header().Set(UserRoleHeader, claims.Role)
			req.Header().Set(UserEmailHeader, claims.Email)

			return next(ctx, req)
		})
	}
	return connect.UnaryInterceptorFunc(interceptor)
}
