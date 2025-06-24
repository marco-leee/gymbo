package queue

import (
	"context"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
)

type ElasticMQQueue struct {
	sqsClient *sqs.Client
}

func NewElasticMQQueue(sqsClient *sqs.Client) *ElasticMQQueue {
	return &ElasticMQQueue{
		sqsClient: sqsClient,
	}
}

func (q *ElasticMQQueue) Enqueue(ctx context.Context, channel string, message []byte) error {
	_, err := q.sqsClient.SendMessage(ctx, &sqs.SendMessageInput{
		QueueUrl:    aws.String(channel),
		MessageBody: aws.String(string(message)),
	})

	if err != nil {
		return err
	}

	return nil
}
