package models

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"

	v1_entities "gymbo.stixman.co/shared/gen/entities/v1"
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

type AnglesOfInterestEnum map[string][]int32

type Angle struct {
	Degree  int32   `json:"degree"`
	Comment *string `json:"comment,omitempty"`
}

type AngleOfInterest map[string]Angle

type AnglesOfInterest []AngleOfInterest

type Landmark2dResult struct {
	Idx     int32   `json:"idx"`
	X       float32 `json:"x"`
	Y       float32 `json:"y"`
	XScores float32 `json:"x_score"`
	YScores float32 `json:"y_score"`
}

type Landmark2dResults [][]Landmark2dResult

type Landmark3dResult struct {
	Idx   int32   `json:"idx"`
	Score float32 `json:"score"`
	X     float32 `json:"x"`
	Y     float32 `json:"y"`
	Z     float32 `json:"z"`
}

type Landmark3dResults [][]Landmark3dResult

// AnglesOfInterestEnum
func (a *AnglesOfInterestEnum) Value() (driver.Value, error) {
	if a == nil {
		return nil, nil
	}
	return json.Marshal(*a)
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
		return fmt.Errorf("type assertion to []byte failed, got type: %T", value)
	}

	return json.Unmarshal(bytes, &a)
}

func (a *AnglesOfInterestEnum) ToProto() *v1_entities.AnglesOfInterestEnum {
	protoEnums := make(map[string]*v1_entities.AnglesOfInterestEnum_Enum)
	for key, value := range *a {
		protoEnums[key] = &v1_entities.AnglesOfInterestEnum_Enum{
			Enum: value,
		}
	}
	return &v1_entities.AnglesOfInterestEnum{
		Enums: protoEnums,
	}
}

// AnglesOfInterest
func (a *Angle) Value() (driver.Value, error) {
	if a == nil {
		return nil, nil
	}
	return json.Marshal(*a)
}

func (a *Angle) Scan(value interface{}) error {
	if value == nil {
		return nil
	}

	var bytes []byte
	switch v := value.(type) {
	case []byte:
		bytes = v
	case string:
		bytes = []byte(v)
	default:
		return fmt.Errorf("type assertion to []byte failed, got type: %T", value)
	}

	return json.Unmarshal(bytes, &a)
}

func (a *AnglesOfInterest) Value() (driver.Value, error) {
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
	case []uint8:
		bytes = v
	case string:
		bytes = []byte(v)
	default:
		return fmt.Errorf("type assertion to []byte failed, got type: %T", value)
	}

	return json.Unmarshal(bytes, &a)
}

func (a *AnglesOfInterest) ToProto() []*v1_entities.AngleOfInterest {
	protoAngles := make([]*v1_entities.AngleOfInterest, len(*a))
	for key, value := range *a {
		k := v1_entities.AngleOfInterest{
			Angles: make(map[string]*v1_entities.Angle),
		}
		for key2, value2 := range value {
			comment := ""
			if value2.Comment != nil {
				comment = *value2.Comment
			}
			k.Angles[key2] = &v1_entities.Angle{
				Degree:  value2.Degree,
				Comment: comment,
			}
		}
		protoAngles[key] = &k
	}

	return protoAngles
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

func (l *Landmark2dResults) ToProto() []*v1_entities.Landmark2DResults {
	protoResults := make([]*v1_entities.Landmark2DResults, len(*l))
	for i, value := range *l {
		protoResults[i] = &v1_entities.Landmark2DResults{
			Results: make([]*v1_entities.Landmark2DResult, len(value)),
		}
		for j, value2 := range value {
			protoResults[i].Results[j] = &v1_entities.Landmark2DResult{
				Idx:    value2.Idx,
				X:      value2.X,
				Y:      value2.Y,
				XScore: value2.XScores,
				YScore: value2.YScores,
			}
		}
	}
	return protoResults
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

func (l *Landmark3dResults) ToProto() []*v1_entities.Landmark3DResults {
	protoResults := make([]*v1_entities.Landmark3DResults, len(*l))
	for i, value := range *l {
		protoResults[i] = &v1_entities.Landmark3DResults{
			Results: make([]*v1_entities.Landmark3DResult, len(value)),
		}
		for j, value2 := range value {
			protoResults[i].Results[j] = &v1_entities.Landmark3DResult{
				Idx:   value2.Idx,
				Score: value2.Score,
				X:     value2.X,
				Y:     value2.Y,
				Z:     value2.Z,
			}
		}
	}
	return protoResults
}
