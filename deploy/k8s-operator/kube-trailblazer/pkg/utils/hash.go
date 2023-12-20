package utils

import (
	"fmt"
	"hash/fnv"

	"github.com/pkg/errors"
)

// FNV64a returns a 64bit hash
func FNV64a(s string) (string, error) {
	h := fnv.New64a()
	if _, err := h.Write([]byte(s)); err != nil {
		return "", errors.Wrap(err, "[FNV64a]\tcould not create hash")
	}
	return fmt.Sprintf("%x", h.Sum64()), nil
}
