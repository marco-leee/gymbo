package admingateway

import (
	"context"
	"fmt"
	"time"

	"connectrpc.com/connect"
	"gymbo.stixman.co/shared/crypto"
	v1 "gymbo.stixman.co/shared/gen/messages/v1"
	"gymbo.stixman.co/shared/interceptors"
)

func (ags *AdminGateway) Login(ctx context.Context, req *connect.Request[v1.LoginRequest]) (*connect.Response[v1.LoginResponse], error) {
	email := req.Msg.Email

	admin, err := ags.db.GetAdminByEmail(ctx, email)

	if err != nil {
		return nil, err
	}

	accessToken, err := ags.tokenManager.GenerateToken(crypto.AuthPayload{
		Id:    admin.ID,
		Email: admin.User.Email,
		Role:  "admin",
	}, time.Hour*3)

	if err != nil {
		return nil, err
	}

	refreshToken, err := ags.tokenManager.GenerateToken(crypto.AuthPayload{
		Id:    admin.ID,
		Email: admin.User.Email,
		Role:  "admin",
	}, time.Hour*24)

	if err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1.LoginResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresAt:    time.Now().Add(time.Hour * 3).Unix(),
	}), nil
}

func (ags *AdminGateway) GetCurrentUser(ctx context.Context, req *connect.Request[v1.GetCurrentUserRequest]) (*connect.Response[v1.GetCurrentUserResponse], error) {
	id := req.Header().Get(interceptors.UserIdHeader)

	fmt.Println("id", id)

	admin, err := ags.db.GetAdminByID(ctx, id)

	if err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1.GetCurrentUserResponse{
		User: &v1.User{
			Id:    admin.ID,
			Email: admin.User.Email,
		},
	}), nil
}

func (ags *AdminGateway) RefreshToken(ctx context.Context, req *connect.Request[v1.RefreshTokenRequest]) (*connect.Response[v1.RefreshTokenResponse], error) {
	refreshToken := req.Msg.RefreshToken

	if err := ags.tokenManager.VerifyToken(refreshToken); err != nil {
		return nil, err
	}

	payload, err := ags.tokenManager.GetPayload(refreshToken)

	if err != nil {
		return nil, err
	}

	admin, err := ags.db.GetAdminByID(ctx, payload.Id)

	if err != nil {
		return nil, err
	}

	accessToken, err := ags.tokenManager.GenerateToken(crypto.AuthPayload{
		Id:    admin.ID,
		Email: admin.User.Email,
		Role:  "admin",
	}, time.Hour*3)

	if err != nil {
		return nil, err
	}

	refreshToken, err = ags.tokenManager.GenerateToken(crypto.AuthPayload{
		Id:    admin.ID,
		Email: admin.User.Email,
		Role:  "admin",
	}, time.Hour*24)

	if err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1.RefreshTokenResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresAt:    time.Now().Add(time.Hour * 3).Unix(),
	}), nil
}
