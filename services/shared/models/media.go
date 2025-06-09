package models

import (
	"database/sql"
	"time"
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
	Metadata               JSONB `gorm:"type:jsonb"`
	Errors                 JSONB `gorm:"type:jsonb"`
	CompletedAt            time.Time
	CreatedAt              time.Time
	UpdatedAt              time.Time
	DeletedAt              sql.NullTime
}
