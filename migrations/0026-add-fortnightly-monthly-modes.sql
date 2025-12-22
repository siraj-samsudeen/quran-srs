-- Migration: Add Fortnightly Reps (FR) and Monthly Reps (MR) modes
-- These modes extend the fixed repetition system beyond Weekly Reps

INSERT INTO modes (code, name, description) VALUES ('FR', 'Fortnightly Reps', 'Fortnightly repetition (14-day interval) after weekly graduation');
INSERT INTO modes (code, name, description) VALUES ('MR', 'Monthly Reps', 'Monthly repetition (30-day interval) after fortnightly graduation');
