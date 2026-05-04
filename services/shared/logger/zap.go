package logger

import "go.uber.org/zap"

func New(name string) *zap.Logger {
	logger, _ := zap.NewProduction()
	return logger.Named(name)
}
