package main

import (
	"context"
	"fmt"

	"gymbo.stixman.co/shared/databases"
	"gymbo.stixman.co/shared/models"
)

func main() {
	dsn := "host=localhost user=admin password=local dbname=gymbo port=32800 sslmode=disable TimeZone=Asia/Hong_Kong"
	postgres := databases.NewPostgres(context.Background(), dsn)

	if err := postgres.Connect(context.Background()); err != nil {
		panic(err)
	}

	tables := []interface{}{
		&models.Users{},
		&models.Admin{},
		&models.Client{},
		&models.Trainer{},
		&models.Organisation{},
		// &models.ClientUser{},
		// &models.TrainerUser{},
		&models.OrganisationUser{},
		&models.OrganisationTrainer{},
		&models.OrganisationClient{},
		&models.ClientTrainer{},
		&models.Assessment{},
		&models.Exercise{},
		&models.Media{},
		&models.ExerciseAssessment{},
	}

	if err := postgres.Migrate(tables...); err != nil {
		panic(err)
	}

	fmt.Println("Migration complete")
}
