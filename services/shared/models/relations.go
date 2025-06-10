package models

import (
	"database/sql"
	"time"
)

type OrganisationUser struct {
	OrganisationID string `gorm:"primaryKey"`
	Organisation   Organisation
	UserID         string `gorm:"primaryKey"`
	User           Users
	CreatedAt      time.Time
	UpdatedAt      time.Time
	DeletedAt      sql.NullTime
}

type TrainerUser struct {
	UserID    string `gorm:"primaryKey"`
	User      Users
	TrainerID string `gorm:"primaryKey"`
	Trainer   Trainer
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}

type ClientUser struct {
	UserID    string `gorm:"primaryKey"`
	User      Users
	ClientID  string `gorm:"primaryKey"`
	Client    Client
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}

type AdminUser struct {
	UserID    string `gorm:"primaryKey"`
	User      Users
	AdminID   string `gorm:"primaryKey"`
	Admin     Admin
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
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

type OrganisationClient struct {
	OrganisationID string `gorm:"primaryKey"`
	Organisation   Organisation
	ClientID       string `gorm:"primaryKey"`
	Client         Client
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
