package models

import (
	"database/sql"
	"time"
)

type Organisation struct {
	ID        string `gorm:"primaryKey"`
	Name      string
	Address   string
	Phone     string
	Email     string
	Logo      string
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}
