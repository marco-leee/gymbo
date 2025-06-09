package models

import (
	"database/sql"
	"time"
)

type OrganisationUser struct {
	OrganisationID string `gorm:"primaryKey"`
	Organisation   Organisation
	UserID         string `gorm:"primaryKey"`
	User           User
	CreatedAt      time.Time
	UpdatedAt      time.Time
	DeletedAt      sql.NullTime
}

type OrganisationTrainer struct {
	OrganisationID string `gorm:"primaryKey"`
	Organisation   Organisation
	TrainerID      string `gorm:"primaryKey"`
	Trainer        Trainer
	CreatedAt      time.Time
	UpdatedAt      time.Time
	DeletedAt      sql.NullTime
}

type ClientTrainer struct {
	ClientID  string `gorm:"primaryKey"`
	Client    Client
	TrainerID string `gorm:"primaryKey"`
	Trainer   Trainer
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}
