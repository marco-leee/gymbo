package models

import (
	"database/sql"
	"time"
)

type Admin struct {
	ID        string `gorm:"primaryKey"`
	UserID    string `gorm:"unique;not null"`
	User      Users
	Password  string `gorm:"not null"`
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}
