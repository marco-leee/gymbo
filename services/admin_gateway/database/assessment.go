package database

import "gymbo.stixman.co/shared/models"

func (ad *AdminGatewayDatabase) getModel() *models.Assessment {
	return &models.Assessment{}
}

func (ad *AdminGatewayDatabase) GetAssessmentByID(id string) (*models.Assessment, error) {
	var assessment models.Assessment
	err := ad.client.GetClient().Model(&models.Assessment{}).Where("id = ?", id).First(&assessment).Error
	return &assessment, err
}

func (ad *AdminGatewayDatabase) ListAssessments(index int32, limit int32, offset int32, filters map[string]string, sort map[string]string) ([]*models.Assessment, error) {
	var assessments []*models.Assessment
	err := ad.client.GetClient().Model(&models.Assessment{}).Where(filters).Order(sort).Offset(int(offset)).Limit(int(limit)).Find(&assessments).Error
	return assessments, err
}

func (ad *AdminGatewayDatabase) GetTotalAssessmentsCount(filters map[string]string) (int64, error) {
	var count int64
	err := ad.client.GetClient().Model(&models.Assessment{}).Where(filters).Count(&count).Error
	return count, err
}

func (ad *AdminGatewayDatabase) CreateAssessment(assessment *models.Assessment) error {
	return ad.client.GetClient().Create(assessment).Error
}

func (ad *AdminGatewayDatabase) UpdateAssessment(assessment *models.Assessment) error {
	return ad.client.GetClient().Save(assessment).Error
}

func (ad *AdminGatewayDatabase) DeleteAssessment(id string) error {
	return ad.client.GetClient().Delete(&models.Assessment{}, id).Error
}

func (ad *AdminGatewayDatabase) GetAssessmentsByExerciseID(exerciseID string) ([]*models.Assessment, error) {
	var assessments []*models.ExerciseAssessment
	err := ad.client.GetClient().Model(&models.ExerciseAssessment{}).Preload("Assessment").Where("exercise_id = ?", exerciseID).Find(&assessments).Error

	if err != nil {
		return nil, err
	}

	protoAssessments := make([]*models.Assessment, len(assessments))
	for i, assessment := range assessments {
		protoAssessments[i] = &assessment.Assessment
	}

	return protoAssessments, nil
}
