package models

import (
	"database/sql"
	"time"
)

type Exercise struct {
	ID                   string `gorm:"primaryKey"`
	ClientID             sql.NullString
	Client               Client
	AssessmentID         sql.NullString
	Assessment           Assessment
	Name                 string
	Description          string
	Type                 string
	Comment              string
	AnglesOfInterestEnum AnglesOfInterestEnum `gorm:"type:jsonb"`
	AnglesOfInterest     AnglesOfInterest     `gorm:"type:jsonb"`
	Landmark2dResults    Landmark2dResults    `gorm:"type:jsonb"`
	Landmark3dResults    Landmark3dResults    `gorm:"type:jsonb"`
	CreatedAt            time.Time
	UpdatedAt            time.Time
	DeletedAt            sql.NullTime
}
