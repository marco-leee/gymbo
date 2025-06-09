package models

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
)

// JSONB is a custom type for handling PostgreSQL JSONB
type JSONB map[string]interface{}

// Value implements the driver.Valuer interface
func (j JSONB) Value() (driver.Value, error) {
	if j == nil {
		return nil, nil
	}
	return json.Marshal(j)
}

// Scan implements the sql.Scanner interface
func (j *JSONB) Scan(value interface{}) error {
	if value == nil {
		*j = nil
		return nil
	}

	var bytes []byte
	switch v := value.(type) {
	case []byte:
		bytes = v
	case string:
		bytes = []byte(v)
	default:
		return errors.New("type assertion to []byte failed")
	}

	return json.Unmarshal(bytes, &j)
}

type AnglesOfInterestEnum map[string]string

type Angle struct {
	Idx    int `json:"idx"`
	Degree int `json:"degree"`
}

type AnglesOfInterest map[int]Angle

type Landmark2dResult struct {
	Idx     int     `json:"idx"`
	X       float32 `json:"x"`
	Y       float32 `json:"y"`
	XScores float32 `json:"x_score"`
	YScores float32 `json:"y_score"`
}

type Landmark2dResults map[int]Landmark2dResult

type Landmark3dResult struct {
	Idx   int     `json:"idx"`
	Score float32 `json:"score"`
	X     float32 `json:"x"`
	Y     float32 `json:"y"`
	Z     float32 `json:"z"`
}

type Landmark3dResults map[int]Landmark3dResult

// AnglesOfInterestEnum
func (a AnglesOfInterestEnum) Value() (driver.Value, error) {
	if a == nil {
		return nil, nil
	}
	return json.Marshal(a)
}

func (a *AnglesOfInterestEnum) Scan(value interface{}) error {
	if value == nil {
		*a = nil
		return nil
	}

	var bytes []byte
	switch v := value.(type) {
	case []byte:
		bytes = v
	case string:
		bytes = []byte(v)
	default:
		return errors.New("type assertion to []byte failed")
	}

	return json.Unmarshal(bytes, &a)
}

// AnglesOfInterest
func (a AnglesOfInterest) Value() (driver.Value, error) {
	if a == nil {
		return nil, nil
	}
	return json.Marshal(a)
}

func (a *AnglesOfInterest) Scan(value interface{}) error {
	if value == nil {
		*a = nil
		return nil
	}

	var bytes []byte
	switch v := value.(type) {
	case []byte:
		bytes = v
	case string:
		bytes = []byte(v)
	default:
		return errors.New("type assertion to []byte failed")
	}

	return json.Unmarshal(bytes, &a)
}

// Landmark2dResults
func (l Landmark2dResults) Value() (driver.Value, error) {
	if l == nil {
		return nil, nil
	}
	return json.Marshal(l)
}

func (l *Landmark2dResults) Scan(value interface{}) error {
	if value == nil {
		*l = nil
		return nil
	}

	var bytes []byte
	switch v := value.(type) {
	case []byte:
		bytes = v
	case string:
		bytes = []byte(v)
	default:
		return errors.New("type assertion to []byte failed")
	}

	return json.Unmarshal(bytes, &l)
}

// Landmark3dResults
func (l Landmark3dResults) Value() (driver.Value, error) {
	if l == nil {
		return nil, nil
	}
	return json.Marshal(l)
}

func (l *Landmark3dResults) Scan(value interface{}) error {
	if value == nil {
		*l = nil
		return nil
	}

	var bytes []byte
	switch v := value.(type) {
	case []byte:
		bytes = v
	case string:
		bytes = []byte(v)
	default:
		return errors.New("type assertion to []byte failed")
	}

	return json.Unmarshal(bytes, &l)
}
