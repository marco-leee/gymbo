package array

import "github.com/samber/lo"

func Contains[T comparable](slice []T, item T) bool {
	return lo.Contains(slice, item)
}
