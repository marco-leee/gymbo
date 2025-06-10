package models

import (
	"database/sql"
	"time"
)

type Trainer struct {
	ID        string `gorm:"primaryKey"`
	UserID    string `gorm:"unique;not null"`
	User      Users
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}
