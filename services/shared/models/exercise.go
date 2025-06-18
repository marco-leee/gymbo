package models

import (
	"database/sql"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
	"gymbo.stixman.co/shared/data_class/str"
	v1_entities "gymbo.stixman.co/shared/gen/entities/v1"
)

type Exercise struct {
	ID           string `gorm:"primaryKey"`
	ClientID     string `gorm:"not null"`
	Client       Client
	AssessmentID *string
	Assessment   Assessment
	Name         string
	Description  string
	Type         string
	Comment      string
	CreatedAt    time.Time
	UpdatedAt    time.Time
	DeletedAt    sql.NullTime
}

func (e *Exercise) BeforeCreate(tx *gorm.DB) (err error) {
	e.ID = str.NewULIDString()
	e.CreatedAt = time.Now()
	e.UpdatedAt = time.Now()
	e.DeletedAt = sql.NullTime{}
	return
}

func (e *Exercise) BeforeUpdate(tx *gorm.DB) (err error) {
	e.UpdatedAt = time.Now()
	return
}

func (e *Exercise) Validate(db *gorm.DB) error {
	// TODO: Validate the exercise
	return nil
}

func (e *Exercise) ToProto() *v1_entities.Exercise {
	return &v1_entities.Exercise{
		Id:           e.ID,
		Name:         e.Name,
		Description:  e.Description,
		Type:         v1_entities.ExerciseType(v1_entities.ExerciseType_value[e.Type]),
		Comment:      e.Comment,
		ClientId:     e.ClientID,
		AssessmentId: e.AssessmentID,
		CreatedAt:    timestamppb.New(e.CreatedAt),
		UpdatedAt:    timestamppb.New(e.UpdatedAt),
		DeletedAt:    timestamppb.New(e.DeletedAt.Time),
	}
}

// func (e *Exercise) ToExtendedProto() *v1_messages.ExtendedExercise {
// 	return &v1_messages.ExtendedExercise{
// 		Exercise: e.ToProto(),
// 		Client:   e.Client.ToProto(),
// 		// Assessments:   e.Assessment.ToProto(),
// 		// Trainer:      e.Trainer.ToProto(),
// 		// Organisation: e.Organisation.ToProto(),
// 	}
// }
