package admingateway

import (
	"context"
	"fmt"
	"strings"

	"connectrpc.com/connect"
	"gymbo.stixman.co/shared/consts"
	"gymbo.stixman.co/shared/data_class/str"
	"gymbo.stixman.co/shared/env"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
	"gymbo.stixman.co/shared/global_error"
	"gymbo.stixman.co/shared/storages"
)

func validateAndFormat(req *connect.Request[v1_messages.SignMediaUploadRequest]) error {
	if !strings.HasPrefix(req.Msg.FileType, "video/") {
		return global_error.AddDetails(global_error.ErrInvalidFileType, "file_name", fmt.Sprintf("File name must start with 'video/'. Found: %s", req.Msg.FileName))
	}

	if req.Msg.FileSize > consts.MAX_FILE_SIZE {
		return global_error.AddDetails(global_error.ErrFileSizeLimitExceeded, "file_size", fmt.Sprintf("File size limit exceeded: %d", consts.MAX_FILE_SIZE))
	}

	formattedName, err := str.RefactorInputFileName(req.Msg.FileName)

	if err != nil {
		return global_error.AddDetails(global_error.ErrInvalidFileName, "file_name", fmt.Sprintf("Invalid file name: %s", req.Msg.FileName))
	}

	req.Msg.FileName = formattedName

	return nil
}

func (as *AdminGateway) SignMediaUpload(ctx context.Context, req *connect.Request[v1_messages.SignMediaUploadRequest]) (*connect.Response[v1_messages.SignMediaUploadResponse], error) {
	if err := validateAndFormat(req); err != nil {
		return nil, err
	}

	ref := &storages.StorageReference{
		StorageReference: v1_messages.StorageReference{
			StorageProvider: v1_messages.StorageProvider_STORAGE_PROVIDER_MINIO,
			Region:          env.StorageRegion,
			Bucket:          env.StorageBucket,
			Key:             fmt.Sprintf("%s/%s/%s", env.StorageBucket, "inputs", req.Msg.FileName),
		},
		ContentType: req.Msg.FileType,
	}

	presignedURL, err := as.storage.PresignUpload(ctx, ref)

	if err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1_messages.SignMediaUploadResponse{
		UploadUrl:        presignedURL,
		StorageReference: &ref.StorageReference,
	}), nil
}
