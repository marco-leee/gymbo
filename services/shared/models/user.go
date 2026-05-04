package models

import (
	"database/sql"
	"time"

	"gorm.io/gorm"
	"gymbo.stixman.co/shared/data_class/str"
	"gymbo.stixman.co/shared/global_error"
)

type Users struct {
	ID        string `gorm:"primaryKey"`
	Email     string `gorm:"unique;not null"`
	FullName  string
	FirstName string
	LastName  string
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}

func (u *Users) BeforeCreate(tx *gorm.DB) (err error) {
	u.ID = str.NewULIDString()
	u.CreatedAt = time.Now()
	u.UpdatedAt = time.Now()
	u.DeletedAt = sql.NullTime{}
	return
}

func (u *Users) BeforeUpdate(tx *gorm.DB) (err error) {
	u.UpdatedAt = time.Now()
	return
}

func (u *Users) IsUnique(db *gorm.DB) (bool, error) {
	var count int64
	err := db.Model(&Users{}).Where("email = ?", u.Email).Count(&count).Error
	return count == 0, err
}

func (u *Users) Validate(db *gorm.DB) error {
	if u.Email == "" {
		return global_error.ErrEmailRequired
	}

	is_unique, err := u.IsUnique(db)

	if err != nil {
		return err
	}

	if !is_unique {
		return global_error.ErrEmailAlreadyInUse
	}

	return nil
}
