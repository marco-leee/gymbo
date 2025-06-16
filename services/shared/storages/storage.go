package storages

import (
	"context"
)

type ObjectStorage interface {
}

type IObjectStorage interface {
	PresignUpload(ctx context.Context, ref *StorageReference) (string, error)
}

func NewObjectStorage(ctx context.Context) (IObjectStorage, error) {
	return NewMinioStorage(ctx)
}
