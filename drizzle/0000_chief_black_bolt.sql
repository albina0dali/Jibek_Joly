CREATE TABLE `samples` (
	`id` text PRIMARY KEY NOT NULL,
	`session` text NOT NULL,
	`owner` text NOT NULL,
	`model_time` real NOT NULL,
	`state` text NOT NULL,
	`created` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `samples_session_time` ON `samples` (`session`,`created`);--> statement-breakpoint
CREATE INDEX `samples_expiry` ON `samples` (`created`);--> statement-breakpoint
CREATE TABLE `sessions` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`state` text NOT NULL,
	`running` integer DEFAULT 0 NOT NULL,
	`version` integer DEFAULT 0 NOT NULL,
	`updated` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `sessions_owner` ON `sessions` (`owner`);--> statement-breakpoint
CREATE TABLE `settings` (
	`id` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL,
	`updated` integer NOT NULL
);
