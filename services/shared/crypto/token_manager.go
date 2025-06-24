package crypto

import (
	"crypto/rsa"
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

const (
	TokenExpiry = time.Minute * 15
)

type AuthPayload struct {
	jwt.RegisteredClaims
	UserId string `json:"user_id"`
	Role   string `json:"role"`
}

type TokenManager struct {
	publicKey  *rsa.PublicKey
	privateKey *rsa.PrivateKey
}

type ITokenManager interface {
	GenerateToken(payload AuthPayload) (string, error)
	VerifyToken(token string) error
	GetPayload(token string) (AuthPayload, error)
}

func NewTokenManager() ITokenManager {
	privateKey, publicKey := GenerateRSAKeyPair()

	return &TokenManager{
		publicKey:  publicKey,
		privateKey: privateKey,
	}
}

func (t *TokenManager) GenerateToken(payload AuthPayload) (string, error) {
	token := jwt.NewWithClaims(jwt.SigningMethodRS256, AuthPayload{
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(TokenExpiry)),
		},
		UserId: payload.UserId,
		Role:   payload.Role,
	})

	return token.SignedString(t.privateKey)
}

func (t *TokenManager) VerifyToken(token string) error {
	parsedToken, err := jwt.Parse(token, func(token *jwt.Token) (interface{}, error) {
		return t.publicKey, nil
	}, jwt.WithValidMethods([]string{"RS256"}))

	switch {
	case parsedToken.Valid:
		return nil
	case errors.Is(err, jwt.ErrTokenMalformed):
	case errors.Is(err, jwt.ErrTokenSignatureInvalid):
	case errors.Is(err, jwt.ErrTokenExpired) || errors.Is(err, jwt.ErrTokenNotValidYet):
	default:
		return err
	}

	return nil
}

func (t *TokenManager) GetPayload(token string) (AuthPayload, error) {
	var payload AuthPayload
	parsedToken, err := jwt.ParseWithClaims(token, &payload, func(token *jwt.Token) (interface{}, error) {
		return t.publicKey, nil
	}, jwt.WithValidMethods([]string{"RS256"}))

	switch {
	case !parsedToken.Valid:
	case errors.Is(err, jwt.ErrTokenMalformed):
	case errors.Is(err, jwt.ErrTokenSignatureInvalid):
	case errors.Is(err, jwt.ErrTokenExpired) || errors.Is(err, jwt.ErrTokenNotValidYet):
	default:
		return payload, err
	}

	claims, ok := parsedToken.Claims.(*AuthPayload)

	if !ok {
		return payload, errors.New("invalid claims")
	}

	return *claims, nil
}
