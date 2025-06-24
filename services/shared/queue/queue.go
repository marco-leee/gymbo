package queue

import (
	"context"
	"fmt"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
)

type IQueue interface {
	Enqueue(ctx context.Context, channel string, message []byte) error
}

func NewQueue(ctx context.Context, name string) (IQueue, error) {
	cfg, err := config.LoadDefaultConfig(ctx)

	if err != nil {
		panic(err)
	}

	switch name {
	case "elastic-mq":
		cfg.Region = "ap-southeast-1"
		cfg.Credentials = credentials.NewStaticCredentialsProvider("", "", "")
		cfg.BaseEndpoint = aws.String("http://localhost:9324")
		sqsClient := sqs.NewFromConfig(cfg)
		return NewElasticMQQueue(sqsClient), nil
	default:
		return nil, fmt.Errorf("queue %s not found", name)
	}
}
