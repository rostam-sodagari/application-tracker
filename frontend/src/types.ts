export interface Application {
  id: string;
  company: string;
  role: string | null;
  source: string | null;
  job_url: string | null;
  cv_file_id: string | null;
  cover_letter_file_id: string | null;
  date_applied: string | null;
  status: string;
  follow_up_date: string | null;
  notes: string | null;
  salary_min: number | null;
  salary_max: number | null;
  location: string | null;
  remote_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationPage {
  items: Application[];
  total: number;
}

export interface CvVersion {
  id: string;
  file_id: string;
  file_name: string;
  company: string | null;
  created_at: string;
}

export interface Meta {
  application_statuses: string[];
}

export interface HomeStats {
  applied_this_week: number;
  weekly_goal_low: number;
  weekly_goal_high: number;
  funnel: Record<string, number>;
  due_follow_ups: Application[];
  total_applications: number;
  total_applied: number;
  response_rate: number | null;
  interview_rate: number | null;
  offer_rate: number | null;
}

export interface Settings {
  user_id: string;
  weekly_goal_low: number;
  weekly_goal_high: number;
}

export type BackendMode = "local" | "appwrite";

export interface PublicConfig {
  backend_mode: BackendMode;
}
