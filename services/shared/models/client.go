package models

import (
	"database/sql"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
	"gymbo.stixman.co/shared/data_class/str"
	v1_entities "gymbo.stixman.co/shared/gen/entities/v1"
	"gymbo.stixman.co/shared/global_error"
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

func (c *Client) BeforeCreate(tx *gorm.DB) (err error) {
	c.ID = str.NewULIDString()
	c.UserID = str.NewULIDString()
	c.User.ID = c.UserID
	c.User.CreatedAt = time.Now()
	c.User.UpdatedAt = time.Now()
	c.User.DeletedAt = sql.NullTime{}
	c.CreatedAt = time.Now()
	c.UpdatedAt = time.Now()
	c.DeletedAt = sql.NullTime{}
	return
}

func (c *Client) BeforeUpdate(tx *gorm.DB) (err error) {
	c.User.UpdatedAt = time.Now()
	c.UpdatedAt = time.Now()
	return
}

func (c *Client) IsUnique(db *gorm.DB) (bool, error) {
	var count int64
	err := db.Model(&c.User).Where("email = ?", c.User.Email).Count(&count).Error

	if err != nil {
		return false, err
	}

	if count > 0 {
		return false, nil
	}

	if c.UserID != "" {
		err = db.Model(&Client{}).Where("user_id = ?", c.UserID).Count(&count).Error

		if err != nil {
			return false, err
		}

		if count > 0 {
			return false, nil
		}
	}

	return true, nil
}

func (c *Client) Validate(db *gorm.DB) error {
	// if c.UserID == "" {
	// 	return global_error.AddDetails(global_error.ErrFieldRequired, "user_id", "user_id is missing")
	// }

	is_unique, err := c.IsUnique(db)

	if err != nil {
		return err
	}

	if !is_unique {
		return global_error.AddDetails(global_error.ErrEmailAlreadyInUse, "user_id", "user_id is already in use")
	}

	return nil
}

func (c *Client) ToProto() *v1_entities.Client {
	return &v1_entities.Client{
		Id:        c.ID,
		Email:     c.User.Email,
		FullName:  c.User.FullName,
		FirstName: &c.User.FirstName,
		LastName:  &c.User.LastName,
		Gender:    c.Gender,
		Height: &v1_entities.Client_Height{
			Value: uint32(c.Height),
			Unit:  "cm",
		},
		Weight: &v1_entities.Client_Weight{
			Value: uint32(c.Weight),
			Unit:  "kg",
		},
		CreatedAt: timestamppb.New(c.CreatedAt),
		UpdatedAt: timestamppb.New(c.UpdatedAt),
		DeletedAt: timestamppb.New(c.DeletedAt.Time),
	}
}

func ToClient(client *v1_entities.Client) *Client {
	return &Client{
		ID: client.Id,
		User: Users{
			Email:     client.Email,
			FullName:  client.FullName,
			FirstName: *client.FirstName,
			LastName:  *client.LastName,
		},
		Gender: client.Gender,
		Height: float64(client.Height.Value),
		Weight: float64(client.Weight.Value),
	}
}

func ClientsToProto(clients []*Client) []*v1_entities.Client {
	protoClients := make([]*v1_entities.Client, len(clients))
	for i, client := range clients {
		protoClients[i] = client.ToProto()
	}
	return protoClients
}
