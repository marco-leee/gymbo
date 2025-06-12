package database

import (
	"gymbo.stixman.co/shared/models"
)

func (ad *AdminGatewayDatabase) CreateOrganisation(organisation *models.Organisation) error {
	return ad.client.GetClient().Create(organisation).Error
}

func (ad *AdminGatewayDatabase) GetOrganisationByID(id string) (*models.Organisation, error) {
	var organisation models.Organisation
	err := ad.client.GetClient().Model(&models.Organisation{}).Where("id = ?", id).First(&organisation).Error
	return &organisation, err
}

func (ad *AdminGatewayDatabase) UpdateOrganisation(organisation *models.Organisation) error {
	return ad.client.GetClient().Save(organisation).Error
}

func (ad *AdminGatewayDatabase) DeleteOrganisation(id string) error {
	return ad.client.GetClient().Delete(&models.Organisation{}, id).Error
}

func (ad *AdminGatewayDatabase) ListOrganisations(index int32, limit int, offset int, filters map[string]string, sort map[string]string) ([]*models.Organisation, error) {
	var organisations []*models.Organisation
	err := ad.client.GetClient().Model(&models.Organisation{}).Where(filters).Order(sort).Offset(offset).Limit(limit).Find(&organisations).Error
	return organisations, err
}

func (ad *AdminGatewayDatabase) GetTotalOrganisationsCount(filters map[string]string) (int64, error) {
	var count int64
	err := ad.client.GetClient().Model(&models.Organisation{}).Where(filters).Count(&count).Error
	return count, err
}
