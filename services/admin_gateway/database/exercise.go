package database

import (
	"gorm.io/gorm/clause"
	"gymbo.stixman.co/shared/models"
)

func (ad *AdminGatewayDatabase) CreateExercise(exercise *models.Exercise) error {
	return ad.client.GetClient().Create(exercise).Error
}

func (ad *AdminGatewayDatabase) GetExerciseByID(id string) (*models.Exercise, error) {
	var exercise models.Exercise
	err := ad.client.GetClient().Model(&models.Exercise{}).Where("id = ?", id).First(&exercise).Error
	return &exercise, err
}

func (ad *AdminGatewayDatabase) UpdateExercise(exercise *models.Exercise) error {
	return ad.client.GetClient().Save(exercise).Error
}

func (ad *AdminGatewayDatabase) DeleteExercise(id string) error {
	return ad.client.GetClient().Delete(&models.Exercise{}, id).Error
}

func (ad *AdminGatewayDatabase) ListExercises(index int32, limit int32, offset int32, filters map[string]string, sort map[string]string) ([]*models.Exercise, error) {
	var exercises []*models.Exercise
	err := ad.client.GetClient().Model(&models.Exercise{}).Preload(clause.Associations).Where(filters).Order(sort).Offset(int(offset)).Limit(int(limit)).Find(&exercises).Error
	return exercises, err
}

func (ad *AdminGatewayDatabase) GetTotalExercisesCount(filters map[string]string) (int64, error) {
	var count int64
	err := ad.client.GetClient().Model(&models.Exercise{}).Where(filters).Count(&count).Error
	return count, err
}
