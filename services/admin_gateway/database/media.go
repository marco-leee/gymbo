package database

import "gymbo.stixman.co/shared/models"

func (ad *AdminGatewayDatabase) CreateMedia(media *models.Media) error {
	return ad.client.GetClient().Create(media).Error
}

func (ad *AdminGatewayDatabase) GetMediaByExerciseID(id string) ([]*models.Media, error) {
	var media []*models.Media
	err := ad.client.GetClient().Model(&models.Media{}).Where("exercise_id = ?", id).Find(&media).Error
	return media, err
}
