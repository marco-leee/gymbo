package admingateway

import (
	"context"
	"fmt"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
	"gymbo.stixman.co/shared/models"
)

func (as *AdminGateway) GetExercise(ctx context.Context, req *connect.Request[v1_messages.GetExerciseRequest]) (*connect.Response[v1_messages.GetExerciseResponse], error) {
	exercise, err := as.db.GetExerciseByID(req.Msg.Id)

	if err != nil {
		return nil, err
	}

	msg := &v1_messages.ExtendedExercise{
		Exercise: exercise.ToProto(),
		Client:   exercise.Client.ToProto(),
	}

	assessments, err := as.db.GetAssessmentsByExerciseID(exercise.ID)

	if err != nil {
		return nil, err
	}

	msg.Assessments = models.AssessmentsToProto(assessments)

	media, err := as.db.GetMediaByExerciseID(exercise.ID)
	if err != nil {
		return nil, err
	}

	msg.Media = models.MediasToProto(media)

	return connect.NewResponse(&v1_messages.GetExerciseResponse{
		Exercise: msg,
	}), nil
}

func (as *AdminGateway) ListExercises(ctx context.Context, req *connect.Request[v1_messages.ListExercisesRequest]) (*connect.Response[v1_messages.ListExercisesResponse], error) {
	exercises, err := as.db.ListExercises(req.Msg.Index, req.Msg.Limit, req.Msg.Offset, req.Msg.Filters, req.Msg.Sort)

	if err != nil {
		return nil, err
	}

	count, err := as.db.GetTotalExercisesCount(req.Msg.Filters)

	if err != nil {
		return nil, err
	}

	extendedExercises := make([]*v1_messages.ExtendedExercise, len(exercises))
	for i, exercise := range exercises {
		extendedExercise := &v1_messages.ExtendedExercise{
			Exercise: exercise.ToProto(),
			Client:   exercise.Client.ToProto(),
			// Assessment:   exercise.Assessment.ToProto(),
			// Trainer:      exercise.Trainer.ToProto(),
			// Organisation: exercise.Organisation.ToProto(),
		}

		extendedExercises[i] = extendedExercise
	}

	return connect.NewResponse(&v1_messages.ListExercisesResponse{
		Exercises: extendedExercises,
		Total:     int32(count),
		Page:      req.Msg.Index,
		Limit:     req.Msg.Limit,
		Offset:    req.Msg.Offset,
	}), nil
}

func (as *AdminGateway) CreateExercise(ctx context.Context, req *connect.Request[v1_messages.CreateExerciseRequest]) (*connect.Response[v1_messages.CreateExerciseResponse], error) {
	reqEx := req.Msg.NewExercise
	newExercise := reqEx.NewExercise
	newMedia := reqEx.NewMedia

	exercise := &models.Exercise{
		Name:         newExercise.Name,
		Comment:      *newExercise.Comment,
		Description:  *newExercise.Description,
		Type:         newExercise.Type.String(),
		ClientID:     newExercise.ClientId,
		AssessmentID: newExercise.AssessmentId,
	}

	if err := exercise.Validate(as.db.GetClient()); err != nil {
		return nil, err
	}

	if err := as.db.CreateExercise(exercise); err != nil {
		return nil, err
	}

	// Validate the media
	for _, m := range newMedia {
		media := &models.Media{
			ExerciseID:            exercise.ID,
			CameraView:            m.CameraView.String(),
			OriginalVideoLocation: m.OriginalVideoLocation,
			// Metadata:              models.JSONB(m.Metadata), // TODO: Add metadata
		}

		if err := media.Validate(as.db.GetClient()); err != nil {
			as.db.DeleteExercise(exercise.ID)
			return nil, err
		}
	}

	// Create the media
	for _, m := range newMedia {
		media := &models.Media{
			ExerciseID:            exercise.ID,
			CameraView:            m.CameraView.String(),
			OriginalVideoLocation: m.OriginalVideoLocation,
			Metadata:              nil,
			// Metadata:              models.JSONB(m.Metadata), // TODO: Add metadata
		}
		if err := as.db.CreateMedia(media); err != nil {
			return nil, err
		}

		// TODO: Encore and send to queue
		msg := models.AsyncMediaProcessingQueueMessage{
			Exercise: exercise.ToProto(),
			Media:    media.ToProto(),
		}
		encoded, err := msg.Encode()
		if err != nil {
			return nil, err
		}
		fmt.Printf("%+v\n", string(encoded))
	}

	return connect.NewResponse(&v1_messages.CreateExerciseResponse{
		Exercise: &v1_messages.ExtendedExercise{
			Exercise: exercise.ToProto(),
		},
	}), nil
}

func (as *AdminGateway) UpdateExercise(ctx context.Context, req *connect.Request[v1_messages.UpdateExerciseRequest]) (*connect.Response[v1_messages.UpdateExerciseResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateExerciseResponse{}), nil
}

func (as *AdminGateway) DeleteExercise(ctx context.Context, req *connect.Request[v1_messages.DeleteExerciseRequest]) (*connect.Response[v1_messages.DeleteExerciseResponse], error) {
	return connect.NewResponse(&v1_messages.DeleteExerciseResponse{}), nil
}
