package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
	"gymbo.stixman.co/shared/data_class/str"
	v1_entities "gymbo.stixman.co/shared/gen/entities/v1"
)

type Media struct {
	ID                     string `gorm:"primaryKey"`
	ExerciseID             string `gorm:"not null"`
	Exercise               Exercise
	Step                   string
	CameraView             string
	OriginalVideoLocation  string
	ProcessedVideoLocation string
	PoseDetectionModelName string
	Metadata               JSONB                `gorm:"type:jsonb"`
	Errors                 JSONB                `gorm:"type:jsonb"`
	AnglesOfInterestEnum   AnglesOfInterestEnum `gorm:"type:jsonb"`
	AnglesOfInterest       AnglesOfInterest     `gorm:"type:jsonb"`
	Landmark2dResults      Landmark2dResults    `gorm:"type:jsonb"`
	Landmark3dResults      Landmark3dResults    `gorm:"type:jsonb"`
	CompletedAt            sql.NullTime
	CreatedAt              time.Time
	UpdatedAt              time.Time
	DeletedAt              sql.NullTime
}

func (m *Media) BeforeCreate(tx *gorm.DB) (err error) {
	m.ID = str.NewULIDString()
	m.Step = v1_entities.Steps_STEP_QUEUING.String()
	m.Errors = nil
	m.ProcessedVideoLocation = v1_entities.MediaPipePoseDetectionModel_MEDIAPIPE_POSE_DETECTION_MODEL_LITE.String()
	m.CreatedAt = time.Now()
	m.UpdatedAt = time.Now()
	m.CompletedAt = sql.NullTime{}
	m.DeletedAt = sql.NullTime{}
	return
}

func (m *Media) BeforeUpdate(tx *gorm.DB) (err error) {
	m.UpdatedAt = time.Now()
	return
}

func (m *Media) Validate(db *gorm.DB) error {
	// TODO: Validate the media
	return nil
}

func (m *Media) ToProto() *v1_entities.Media {
	return &v1_entities.Media{
		Id:                     m.ID,
		ExerciseId:             m.ExerciseID,
		Step:                   v1_entities.Steps(v1_entities.Steps_value[m.Step]),
		CameraView:             v1_entities.CameraView(v1_entities.CameraView_value[m.CameraView]),
		OriginalVideoLocation:  m.OriginalVideoLocation,
		ProcessedVideoLocation: m.ProcessedVideoLocation,
		PoseDetectionModelName: m.PoseDetectionModelName,
		// Metadata:               m.Metadata,
		// Errors:                 m.Errors,
		AnglesOfInterestEnum: m.AnglesOfInterestEnum.ToProto(),
		AnglesOfInterest:     m.AnglesOfInterest.ToProto(),
		Landmark_2DResults:   m.Landmark2dResults.ToProto(),
		Landmark_3DResults:   m.Landmark3dResults.ToProto(),
		CompletedAt:          timestamppb.New(m.CompletedAt.Time),
		CreatedAt:            timestamppb.New(m.CreatedAt),
		UpdatedAt:            timestamppb.New(m.UpdatedAt),
		DeletedAt:            timestamppb.New(m.DeletedAt.Time),
	}
}

func MediasToProto(media []*Media) []*v1_entities.Media {
	protoMedia := make([]*v1_entities.Media, len(media))
	for i, m := range media {
		protoMedia[i] = m.ToProto()
	}
	return protoMedia
}

type AsyncMediaProcessingQueueMessage v1_entities.AsyncMediaProcessingQueueMessage

func (m *AsyncMediaProcessingQueueMessage) Encode() ([]byte, error) {
	return json.Marshal(m)
}
