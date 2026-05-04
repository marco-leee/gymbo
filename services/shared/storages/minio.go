package storages

import (
	"context"
	"errors"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"gymbo.stixman.co/shared/env"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
)

type MinioStorage struct {
	client *s3.Client
}

type StorageReference struct {
	v1_messages.StorageReference
	ContentType string
}

func (s *StorageReference) Validate() error {
	if s.Bucket == "" {
		return errors.New("bucket is required")
	}

	return nil
}

func NewMinioStorage(ctx context.Context) (*MinioStorage, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		panic(err)
	}

	cfg.Region = "ap-southeast-1"
	cfg.Credentials = credentials.NewStaticCredentialsProvider(env.StorageAccessKey, env.StorageSecretKey, "")
	cfg.BaseEndpoint = &env.StorageEndpoint

	client := s3.NewFromConfig(cfg)

	return &MinioStorage{
		client: client,
	}, nil
}

func (s *MinioStorage) GetClient() *s3.Client {
	return s.client
}

func (s *MinioStorage) PresignUpload(ctx context.Context, ref *StorageReference) (string, error) {
	presignClient := s3.NewPresignClient(s.client)

	presignedURL, err := presignClient.PresignPutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(ref.Bucket),
		Key:    aws.String(ref.Key),
	})

	if err != nil {
		return "", err
	}

	return presignedURL.URL, nil
}
