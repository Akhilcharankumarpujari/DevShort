package database

import (
	"fmt"

	"gorm.io/gorm"
)

// SystemSetting represents a baseline configuration table for testing migrations and seeders
type SystemSetting struct {
	Key   string `gorm:"primaryKey;size:100"`
	Value string `gorm:"size:255"`
}

func Seed(db *gorm.DB) error {
	// Automatically migrate the baseline seeding model
	if err := db.AutoMigrate(&SystemSetting{}); err != nil {
		return fmt.Errorf("failed to auto migrate seed tables: %w", err)
	}

	// Prepare default platform settings
	settings := []SystemSetting{
		{Key: "platform_name", Value: "Zidoc"},
		{Key: "allowed_upload_types", Value: "pdf,jpeg,png,tiff"},
		{Key: "session_timeout_minutes", Value: "30"},
	}

	for _, setting := range settings {
		err := db.FirstOrCreate(&setting, SystemSetting{Key: setting.Key}).Error
		if err != nil {
			return fmt.Errorf("failed to seed platform setting key '%s': %w", setting.Key, err)
		}
	}

	return nil
}
