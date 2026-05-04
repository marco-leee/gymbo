CREATE KEYSPACE IF NOT EXISTS exercise_analyser WITH REPLICATION = { 
  'class' : 'SimpleStrategy', 
  'replication_factor' : 1
};

CREATE TYPE IF NOT EXISTS exercise_analyser.landmark_result_2d (
  landmark_index int,
  x float,
  y float,
  x_score float,
  y_score float,
);

CREATE TYPE IF NOT EXISTS exercise_analyser.landmark_result_3d (
  landmark_index int,
  score float,
  x float,
  y float,
  z float,
);

CREATE TYPE IF NOT EXISTS exercise_analyser.angle_of_interest (
  idx tinyint,
  degree smallint,
);

CREATE TABLE IF NOT EXISTS exercise_analyser.organisers_by_id (
  id varchar,
  first_name varchar,
  last_name varchar,
  email varchar,
  created_at timestamp,
  updated_at timestamp,
  PRIMARY KEY ((id), created_at)
) WITH COMMENT = 'select * from exercise_analyser.organisers_by_id where id = ?'
    AND CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS exercise_analyser.organisers_login_by_email_password (
  organiser_id varchar,
  email varchar,
  password varchar,
  PRIMARY KEY ((email))
) WITH COMMENT = 'select * from exercise_analyser.organiser_login_by_email_password where email = ?';

-- CREATE TABLE IF NOT EXISTS exercise_analyser.trainers_in_organiser (
--   organiser_id varchar,
--   trainer_id varchar,
--   PRIMARY KEY ((organiser_id))
-- );

CREATE TABLE IF NOT EXISTS exercise_analyser.clients_by_id (
  id varchar,
  first_name varchar,
  last_name varchar,
  email varchar,
  created_at timestamp,
  updated_at timestamp,
  PRIMARY KEY ((id), created_at)
) WITH COMMENT = 'select * from exercise_analyser.clients_by_id where id = ?'
    AND CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS exercise_analyser.clients_by_email (
  client_id varchar,
  email varchar,
  PRIMARY KEY ((email))
) WITH COMMENT = 'select * from exercise_analyser.clients_by_email where email = ?';

CREATE TABLE IF NOT EXISTS exercise_analyser.trainers_by_id (
  id varchar,
  first_name varchar,
  last_name varchar,
  email varchar,
  created_at timestamp,
  updated_at timestamp,
  PRIMARY KEY ((id), created_at)
) WITH COMMENT = 'select * from exercise_analyser.trainers where id = ?'
    AND CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS exercise_analyser.trainers_by_email (
  trainer_id varchar,
  email varchar,
  PRIMARY KEY ((email))
) WITH COMMENT = 'select * from exercise_analyser.trainers_by_email where email = ?';


-- CREATE TABLE IF NOT EXISTS exercise_analyser.clients_in_trainer (
--   trainer_id varchar,
--   client_id varchar,
--   PRIMARY KEY ((trainer_id))
-- );

CREATE TABLE IF NOT EXISTS exercise_analyser.exercises_by_id (
  id varchar,
  name varchar,
  description text,
  type varchar,
  client_id varchar,
  trainer_id varchar,
  comment text,
  created_at timestamp,
  updated_at timestamp,
  PRIMARY KEY ((id), created_at)
) WITH COMMENT = 'select * from exercise_analyser.exercises_by_id where id = ? and created_at between ? and ?'
    AND CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS exercise_analyser.exercises_by_client_id_date (
  exercise_id varchar,
  client_id varchar,
  created_at timestamp,
  PRIMARY KEY ((client_id), created_at)
) WITH COMMENT = 'select * from exercise_analyser.exercises_by_client_id_date where client_id = ? and created_at between ? and ?'
    AND CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS exercise_analyser.media_by_id (
  id varchar,
  exercise_id varchar,
  original_video_location varchar,
  processed_video_location varchar,
  step varchar,
  camera_view varchar,
  pose_detection_model_name varchar,
  metadata map<varchar, varchar>,
  errors map<varchar, varchar>,
  angles_of_interest_enum frozen<map<int, varchar>>,
  angles_of_interest frozen<map<int, set<angle_of_interest>>>,
  landmark_results_2d frozen<map<int, landmark_result_2d>>,
  landmark_results_3d frozen<map<int, landmark_result_3d>>,
  created_at timestamp,
  updated_at timestamp,
  completed_at timestamp,
  PRIMARY KEY ((id), created_at)
) WITH COMMENT = 'select * from exercise_analyser.media where id = ? and created_at between ? and ?'
    AND CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS exercise_analyser.media_by_exercise_id (
  media_id varchar,
  exercise_id varchar,
  PRIMARY KEY ((exercise_id))
) WITH COMMENT = 'select * from exercise_analyser.media_by_exercise_id where exercise_id = ?';
