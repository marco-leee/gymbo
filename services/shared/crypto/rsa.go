package crypto

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
)

func GenerateRSAKeyPair() (*rsa.PrivateKey, *rsa.PublicKey) {
	rsaKey, err := rsa.GenerateKey(rand.Reader, 4096)

	if err != nil {
		panic(err)
	}

	return rsaKey, rsaKey.Public().(*rsa.PublicKey)
}

func ExportRSAKeyPair(rsaKey *rsa.PrivateKey) (string, string) {
	privateKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(rsaKey),
	})

	pubKey, err := x509.MarshalPKIXPublicKey(rsaKey.Public())

	if err != nil {
		panic(err)
	}

	pubKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PUBLIC KEY",
		Bytes: pubKey,
	})

	return string(privateKeyPEM), string(pubKeyPEM)
}
