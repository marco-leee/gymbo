package str

import (
	"errors"
	"fmt"
	"strings"
)

func RefactorInputFileName(fileName string) (string, error) {
	parts := strings.Split(fileName, ".")

	if len(parts) != 2 {
		return "", errors.New("invalid file name")
	}

	extension := parts[len(parts)-1]

	return fmt.Sprintf("%s.%s", strings.ToLower(NewULID().String()), strings.ToLower(extension)), nil
}
