package database

import (
	"context"

	"gymbo.stixman.co/shared/global_error"
	"gymbo.stixman.co/shared/models"
)

func (ad *AdminGatewayDatabase) GetAdminByID(ctx context.Context, id string) (*models.Admin, error) {
	var admin models.Admin

	client := ad.client.GetClient()

	if err := client.InnerJoins("User").Find(&admin, "Admin.id = ?", id).Error; err != nil {
		return nil, err
	}

	if admin.ID == "" {
		return nil, global_error.AddDetails(global_error.ErrEntityNotFound, "db.admin", "admin not found")
	}

	return &admin, nil
}

func (ad *AdminGatewayDatabase) GetAdminByEmail(ctx context.Context, email string) (*models.Admin, error) {
	var admin models.Admin

	client := ad.client.GetClient()

	if err := client.InnerJoins("User", client.Where(&models.Users{Email: email})).Find(&admin).Error; err != nil {
		return nil, err
	}

	if admin.ID == "" {
		return nil, global_error.AddDetails(global_error.ErrEntityNotFound, "db.admin", "admin not found")
	}

	return &admin, nil
}
