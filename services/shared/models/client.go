package models

import (
	"database/sql"
	"time"
)

type Client struct {
	ID        string `gorm:"primaryKey"`
	UserID    string `gorm:"unique;not null"`
	User      Users
	Gender    string
	Height    float64
	Weight    float64
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}
