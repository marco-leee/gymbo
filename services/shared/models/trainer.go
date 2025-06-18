package models

import (
	"database/sql"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"
	v1_entities "gymbo.stixman.co/shared/gen/entities/v1"
)

type Trainer struct {
	ID        string `gorm:"primaryKey"`
	UserID    string `gorm:"unique;not null"`
	User      Users
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}

func (t *Trainer) ToProto() *v1_entities.Trainer {
	return &v1_entities.Trainer{
		Id:        t.ID,
		FullName:  t.User.FullName,
		FirstName: &t.User.FirstName,
		LastName:  &t.User.LastName,
		Email:     t.User.Email,
		CreatedAt: timestamppb.New(t.CreatedAt),
		UpdatedAt: timestamppb.New(t.UpdatedAt),
		DeletedAt: timestamppb.New(t.DeletedAt.Time),
	}
}
