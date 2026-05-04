package models

import (
	"database/sql"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"
	v1_entities "gymbo.stixman.co/shared/gen/entities/v1"
)

type Assessment struct {
	ID             string `gorm:"primaryKey"`
	ClientID       string `gorm:"not null"`
	Client         Client
	TrainerID      string `gorm:"not null"`
	Trainer        Trainer
	OrganisationID string
	Organisation   Organisation
	Date           time.Time
	Comment        sql.NullString
	CreatedAt      time.Time
	UpdatedAt      time.Time
	DeletedAt      sql.NullTime
}

func (a *Assessment) ToProto() *v1_entities.Assessment {
	return &v1_entities.Assessment{
		Id:             a.ID,
		ClientId:       a.ClientID,
		TrainerId:      a.TrainerID,
		OrganisationId: &a.OrganisationID,
		Date:           timestamppb.New(a.Date),
		Comment:        a.Comment.String,
		CreatedAt:      timestamppb.New(a.CreatedAt),
		UpdatedAt:      timestamppb.New(a.UpdatedAt),
		DeletedAt:      timestamppb.New(a.DeletedAt.Time),
	}
}

func AssessmentsToProto(assessments []*Assessment) []*v1_entities.Assessment {
	protoAssessments := make([]*v1_entities.Assessment, len(assessments))
	for i, assessment := range assessments {
		protoAssessments[i] = assessment.ToProto()
	}
	return protoAssessments
}
