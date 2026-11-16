/*M!999999\- enable the sandbox mode */ 
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `appliances` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(120) NOT NULL,
  `category` varchar(40) NOT NULL,
  `brand` varchar(80) DEFAULT NULL,
  `model_number` varchar(80) DEFAULT NULL,
  `purchase_date` date DEFAULT NULL,
  `installation_date` date DEFAULT NULL,
  `warranty_expiry` date DEFAULT NULL,
  `expected_lifespan_years` float NOT NULL,
  `last_service_date` date DEFAULT NULL,
  `usage_frequency` varchar(20) NOT NULL,
  `condition` varchar(20) NOT NULL,
  `location` varchar(80) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `health_score` float DEFAULT NULL,
  `risk_level` varchar(20) DEFAULT NULL,
  `next_service_date` date DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_appliances_user_category` (`user_id`,`category`),
  KEY `ix_appliances_user_id` (`user_id`),
  KEY `ix_appliances_user_risk` (`user_id`,`risk_level`),
  KEY `ix_appliances_warranty_expiry` (`warranty_expiry`),
  CONSTRAINT `appliances_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `session_id` varchar(64) NOT NULL,
  `role` varchar(20) NOT NULL,
  `message` text NOT NULL,
  `source` varchar(20) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_chat_user_session` (`user_id`,`session_id`),
  CONSTRAINT `chat_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `expenses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `appliance_id` int(11) DEFAULT NULL,
  `expense_type` varchar(20) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `expense_date` date NOT NULL,
  `vendor` varchar(120) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_expenses_appliance_id` (`appliance_id`),
  KEY `ix_expenses_user_date` (`user_id`,`expense_date`),
  CONSTRAINT `expenses_ibfk_1` FOREIGN KEY (`appliance_id`) REFERENCES `appliances` (`id`) ON DELETE SET NULL,
  CONSTRAINT `expenses_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `maintenance_records` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `appliance_id` int(11) NOT NULL,
  `schedule_id` int(11) DEFAULT NULL,
  `service_date` date NOT NULL,
  `maintenance_type` varchar(40) NOT NULL,
  `description` text DEFAULT NULL,
  `technician` varchar(120) DEFAULT NULL,
  `cost` decimal(10,2) NOT NULL,
  `was_breakdown` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `schedule_id` (`schedule_id`),
  KEY `ix_maintenance_records_user_id` (`user_id`),
  KEY `ix_records_appliance_date` (`appliance_id`,`service_date`),
  CONSTRAINT `maintenance_records_ibfk_1` FOREIGN KEY (`appliance_id`) REFERENCES `appliances` (`id`) ON DELETE CASCADE,
  CONSTRAINT `maintenance_records_ibfk_2` FOREIGN KEY (`schedule_id`) REFERENCES `maintenance_schedules` (`id`) ON DELETE SET NULL,
  CONSTRAINT `maintenance_records_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `maintenance_schedules` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `appliance_id` int(11) NOT NULL,
  `title` varchar(160) NOT NULL,
  `maintenance_type` varchar(40) NOT NULL,
  `scheduled_at` datetime NOT NULL,
  `description` text DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `technician` varchar(120) DEFAULT NULL,
  `estimated_cost` decimal(10,2) DEFAULT NULL,
  `is_ai_suggested` tinyint(1) NOT NULL,
  `completed_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_maintenance_schedules_appliance_id` (`appliance_id`),
  KEY `ix_schedules_user_date` (`user_id`,`scheduled_at`),
  KEY `ix_schedules_user_status` (`user_id`,`status`),
  CONSTRAINT `maintenance_schedules_ibfk_1` FOREIGN KEY (`appliance_id`) REFERENCES `appliances` (`id`) ON DELETE CASCADE,
  CONSTRAINT `maintenance_schedules_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `type` varchar(40) NOT NULL,
  `severity` varchar(20) NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `link` varchar(255) DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL,
  `emailed` tinyint(1) NOT NULL,
  `dedupe_key` varchar(160) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_notifications_user_dedupe` (`user_id`,`dedupe_key`),
  KEY `ix_notifications_user_read` (`user_id`,`is_read`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `prediction_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `appliance_id` int(11) NOT NULL,
  `health_score` float NOT NULL,
  `risk_level` varchar(20) NOT NULL,
  `priority` varchar(60) NOT NULL,
  `recommended_service_date` date NOT NULL,
  `model_used` varchar(40) NOT NULL,
  `confidence` float DEFAULT NULL,
  `explanation` text NOT NULL,
  `features` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_prediction_history_user_id` (`user_id`),
  KEY `ix_predictions_appliance_created` (`appliance_id`,`created_at`),
  CONSTRAINT `prediction_history_ibfk_1` FOREIGN KEY (`appliance_id`) REFERENCES `appliances` (`id`) ON DELETE CASCADE,
  CONSTRAINT `prediction_history_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=94 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `reported_issues` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `appliance_id` int(11) NOT NULL,
  `problem_category` varchar(60) NOT NULL,
  `description` text NOT NULL,
  `severity` varchar(20) NOT NULL,
  `priority` varchar(10) NOT NULL,
  `status` varchar(20) NOT NULL,
  `reported_date` date NOT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `ai_suggestions` text DEFAULT NULL,
  `suggestion_source` varchar(20) DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `ix_issues_user_status` (`user_id`,`status`),
  KEY `ix_reported_issues_appliance_id` (`appliance_id`),
  CONSTRAINT `reported_issues_ibfk_1` FOREIGN KEY (`appliance_id`) REFERENCES `appliances` (`id`) ON DELETE CASCADE,
  CONSTRAINT `reported_issues_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(120) NOT NULL,
  `email` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `address` varchar(500) DEFAULT NULL,
  `household_name` varchar(120) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `email_notifications` tinyint(1) NOT NULL,
  `token_version` int(11) NOT NULL,
  `reset_token_hash` varchar(128) DEFAULT NULL,
  `reset_token_expires` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  KEY `ix_users_reset_token_hash` (`reset_token_hash`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
