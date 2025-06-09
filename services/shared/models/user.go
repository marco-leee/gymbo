package models

import (
	"database/sql"
	"time"
)

type User struct {
	ID        string `gorm:"primaryKey"`
	Email     string `gorm:"unique;not null"`
	FullName  string
	FirstName string
	LastName  string
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}
