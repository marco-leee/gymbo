package database

import "gymbo.stixman.co/shared/models"

func (ad *AdminGatewayDatabase) CreateClient(client *models.Client) error {
	return ad.client.GetClient().Create(client).Error
}

func (ad *AdminGatewayDatabase) GetClientByID(id string) (*models.Client, error) {
	var client models.Client
	err := ad.client.GetClient().Model(&models.Client{}).Preload("User").Where("id = ?", id).First(&client).Error
	return &client, err
}

func (ad *AdminGatewayDatabase) GetClientByUserID(id string) (*models.Client, error) {
	var client models.Client
	err := ad.client.GetClient().Model(&models.Client{}).Preload("User").Where("user_id = ?", id).First(&client).Error
	return &client, err
}

func (ad *AdminGatewayDatabase) UpdateClient(client *models.Client) error {
	return ad.client.GetClient().Save(client).Error
}

func (ad *AdminGatewayDatabase) DeleteClient(id string) error {
	return ad.client.GetClient().Delete(&models.Client{}, id).Error
}

func (ad *AdminGatewayDatabase) ListClients(index int32, limit int, offset int, filters map[string]string, sort map[string]string) ([]*models.Client, error) {
	var clients []*models.Client
	err := ad.client.GetClient().Model(&models.Client{}).
		Preload("User").
		Where(filters).
		Order(sort).
		Offset(offset).
		Limit(limit).
		Find(&clients).Error
	return clients, err
}

func (ad *AdminGatewayDatabase) GetTotalClientsCount(filters map[string]string) (int64, error) {
	var count int64
	err := ad.client.GetClient().Model(&models.Client{}).Preload("User").Where(filters).Count(&count).Error
	return count, err
}
