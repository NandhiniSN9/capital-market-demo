export interface SendMessageRequestDTO {
  session_id?: string;
  session_title?: string;
  agent_type?: string;
  analyst_type: string;
  scenario_type: string;
  content: string;
}
