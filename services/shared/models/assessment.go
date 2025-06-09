package models

import (
	"database/sql"
	"time"
)

type Assessment struct {
	ID        string `gorm:"primaryKey"`
	ClientID  string `gorm:"not null"`
	Client    Client
	TrainerID string `gorm:"not null"`
	Trainer   Trainer
	Date      time.Time
	Comment   sql.NullString
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}
