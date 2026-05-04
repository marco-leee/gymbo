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

type Organisation struct {
	ID        string `gorm:"primaryKey"`
	Email     string `gorm:"unique; not null"`
	Name      string
	Address   string
	Phone     string
	Logo      string
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt sql.NullTime
}

func (o *Organisation) BeforeCreate(tx *gorm.DB) (err error) {
	o.ID = str.NewULIDString()
	o.CreatedAt = time.Now()
	o.UpdatedAt = time.Now()
	o.DeletedAt = sql.NullTime{}
	return
}

func (o *Organisation) BeforeUpdate(tx *gorm.DB) (err error) {
	o.UpdatedAt = time.Now()
	return
}

func (o *Organisation) IsUnique(db *gorm.DB) (bool, error) {
	var count int64
	err := db.Model(&Organisation{}).Where("email = ?", o.Email).Count(&count).Error
	return count == 0, err
}

func (o *Organisation) Validate(db *gorm.DB) error {
	if o.Email == "" {
		return global_error.ErrEmailRequired
	}

	is_unique, err := o.IsUnique(db)

	if err != nil {
		return err
	}

	if !is_unique {
		return global_error.ErrEmailAlreadyInUse
	}

	return nil
}

func (o *Organisation) ToProto() *v1_entities.Organisation {
	return &v1_entities.Organisation{
		Id:        o.ID,
		Email:     o.Email,
		Name:      o.Name,
		Address:   o.Address,
		Phone:     o.Phone,
		Logo:      o.Logo,
		CreatedAt: timestamppb.New(o.CreatedAt),
		UpdatedAt: timestamppb.New(o.UpdatedAt),
		DeletedAt: timestamppb.New(o.DeletedAt.Time),
	}
}

func OrganisationsToProto(organisations []*Organisation) []*v1_entities.Organisation {
	protoOrganisations := make([]*v1_entities.Organisation, len(organisations))
	for i, organisation := range organisations {
		protoOrganisations[i] = organisation.ToProto()
	}
	return protoOrganisations
}

// var organisationSchema = z.Struct(z.Shape{
// 	"ID":        z.String(),
// 	"Email":     z.String().Email(),
// 	"Name":      z.String().Optional(),
// 	"Address":   z.String().Optional(),
// 	"Phone":     z.String().Optional(),
// 	"Logo":      z.String().Optional(),
// 	"CreatedAt": z.Time().Default(time.Now()),
// 	"UpdatedAt": z.Time().Default(time.Now()),
// 	"DeletedAt": z.Time().Default(time.Now()),
// })
