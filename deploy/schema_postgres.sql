-- =============================================================================
-- NWIS Production Database Schema — PostgreSQL 15+ / PostGIS / pgvector
-- Compiled for Oil India Limited (eRTMAC-NWIS Testbed)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Table: advisory_events
CREATE TABLE advisory_events (
	advisory_id VARCHAR(64) NOT NULL, 
	session_id VARCHAR(64), 
	target_well_id VARCHAR(64) NOT NULL, 
	timestamp VARCHAR(32), 
	bit_depth_md_m FLOAT NOT NULL, 
	bit_depth_tvdss_m FLOAT NOT NULL, 
	formation_name VARCHAR(64) NOT NULL, 
	advisory_state VARCHAR(64), 
	risk_category VARCHAR(64) NOT NULL, 
	risk_score FLOAT NOT NULL, 
	lead_distance_m FLOAT, 
	source_wells_json TEXT NOT NULL, 
	explanation TEXT NOT NULL, 
	evidence_passport_json TEXT, 
	human_review_status VARCHAR(32), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (advisory_id)
);

CREATE INDEX ix_advisory_events_session_id ON advisory_events (session_id);
CREATE INDEX ix_advisory_events_target_well_id ON advisory_events (target_well_id);
CREATE INDEX ix_advisory_events_advisory_id ON advisory_events (advisory_id);

-- Table: analogue_candidates
CREATE TABLE analogue_candidates (
	candidate_id VARCHAR(64) NOT NULL, 
	primary_wellbore_id VARCHAR(64) NOT NULL, 
	offset_wellbore_id VARCHAR(64) NOT NULL, 
	distance_km FLOAT NOT NULL, 
	field_match BOOLEAN, 
	formation_overlap BOOLEAN, 
	trajectory_match VARCHAR(32), 
	eligibility_status VARCHAR(32), 
	exclusion_reason VARCHAR(255), 
	PRIMARY KEY (candidate_id)
);

CREATE INDEX ix_analogue_candidates_primary_wellbore_id ON analogue_candidates (primary_wellbore_id);
CREATE INDEX ix_analogue_candidates_candidate_id ON analogue_candidates (candidate_id);
CREATE INDEX ix_analogue_candidates_offset_wellbore_id ON analogue_candidates (offset_wellbore_id);

-- Table: analogue_evaluations
CREATE TABLE analogue_evaluations (
	evaluation_id VARCHAR(64) NOT NULL, 
	primary_wellbore_id VARCHAR(64) NOT NULL, 
	offset_wellbore_id VARCHAR(64) NOT NULL, 
	geological_similarity_score FLOAT NOT NULL, 
	operational_similarity_score FLOAT NOT NULL, 
	spatial_proximity_score FLOAT NOT NULL, 
	composite_score FLOAT NOT NULL, 
	explanation_json TEXT NOT NULL, 
	rank_order INTEGER, 
	evaluation_timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (evaluation_id)
);

CREATE INDEX ix_analogue_evaluations_evaluation_id ON analogue_evaluations (evaluation_id);
CREATE INDEX ix_analogue_evaluations_offset_wellbore_id ON analogue_evaluations (offset_wellbore_id);
CREATE INDEX ix_analogue_evaluations_primary_wellbore_id ON analogue_evaluations (primary_wellbore_id);

-- Table: audit_events
CREATE TABLE audit_events (
	id SERIAL NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	user_id VARCHAR(64) NOT NULL, 
	action VARCHAR(64) NOT NULL, 
	resource_type VARCHAR(64) NOT NULL, 
	resource_id VARCHAR(64) NOT NULL, 
	details_json TEXT, 
	integrity_hmac VARCHAR(64), 
	PRIMARY KEY (id)
);

CREATE INDEX ix_audit_events_timestamp ON audit_events (timestamp);
CREATE INDEX ix_audit_events_user_id ON audit_events (user_id);

-- Table: audit_logs
CREATE TABLE audit_logs (
	id SERIAL NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	user_id VARCHAR(64) NOT NULL, 
	action VARCHAR(64) NOT NULL, 
	resource_type VARCHAR(64) NOT NULL, 
	resource_id VARCHAR(64) NOT NULL, 
	details_json TEXT, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);

-- Table: data_sources
CREATE TABLE data_sources (
	source_id VARCHAR(64) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	source_type VARCHAR(64), 
	base_url VARCHAR(255), 
	country VARCHAR(64), 
	basin VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (source_id)
);

CREATE INDEX ix_data_sources_source_id ON data_sources (source_id);

-- Table: document_extractions
CREATE TABLE document_extractions (
	id SERIAL NOT NULL, 
	doc_name VARCHAR(255) NOT NULL, 
	page_number INTEGER NOT NULL, 
	section_type VARCHAR(64) NOT NULL, 
	extracted_text TEXT NOT NULL, 
	extracted_json TEXT, 
	ocr_confidence_score FLOAT NOT NULL, 
	review_status VARCHAR(20), 
	reviewed_by VARCHAR(64), 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);


-- Table: engineering_rule_versions
CREATE TABLE engineering_rule_versions (
	rule_id VARCHAR(64) NOT NULL, 
	rule_name VARCHAR(128) NOT NULL, 
	rule_version VARCHAR(32), 
	hazard_type VARCHAR(64) NOT NULL, 
	conditions_json TEXT NOT NULL, 
	required_channels_json TEXT NOT NULL, 
	hysteresis_window_s INTEGER, 
	cooldown_s INTEGER, 
	approved_by VARCHAR(64), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (rule_id)
);

CREATE INDEX ix_engineering_rule_versions_hazard_type ON engineering_rule_versions (hazard_type);
CREATE INDEX ix_engineering_rule_versions_rule_id ON engineering_rule_versions (rule_id);

-- Table: evaluation_runs
CREATE TABLE evaluation_runs (
	run_id VARCHAR(64) NOT NULL, 
	target_well_id VARCHAR(64) NOT NULL, 
	evaluation_type VARCHAR(64), 
	lookahead_window_m FLOAT, 
	cooldown_window_m FLOAT, 
	total_events INTEGER, 
	true_positives INTEGER, 
	false_positives INTEGER, 
	false_negatives INTEGER, 
	abstentions INTEGER, 
	precision FLOAT, 
	recall FLOAT, 
	f1_score FLOAT, 
	false_alarms_per_100m FLOAT, 
	avg_lead_distance_m FLOAT, 
	execution_timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (run_id)
);

CREATE INDEX ix_evaluation_runs_run_id ON evaluation_runs (run_id);
CREATE INDEX ix_evaluation_runs_target_well_id ON evaluation_runs (target_well_id);

-- Table: fields
CREATE TABLE fields (
	field_id VARCHAR(64) NOT NULL, 
	field_name VARCHAR(128) NOT NULL, 
	country VARCHAR(64), 
	basin VARCHAR(128), 
	operator VARCHAR(64), 
	discovery_year INTEGER, 
	description TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (field_id)
);

CREATE INDEX ix_fields_field_id ON fields (field_id);
CREATE UNIQUE INDEX ix_fields_field_name ON fields (field_name);

-- Table: formations
CREATE TABLE formations (
	formation_id VARCHAR(64) NOT NULL, 
	formation_name VARCHAR(128) NOT NULL, 
	stratigraphic_group VARCHAR(128) NOT NULL, 
	geological_age VARCHAR(64), 
	primary_lithology VARCHAR(64), 
	typical_thickness_m FLOAT, 
	reservoir_potential VARCHAR(32), 
	color_code VARCHAR(16), 
	description TEXT, 
	PRIMARY KEY (formation_id)
);

CREATE INDEX ix_formations_formation_id ON formations (formation_id);
CREATE UNIQUE INDEX ix_formations_formation_name ON formations (formation_name);

-- Table: generation_audits
CREATE TABLE generation_audits (
	audit_id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64), 
	query_text TEXT NOT NULL, 
	plan_id VARCHAR(64), 
	retrieval_status VARCHAR(64), 
	evidence_chunks_count INTEGER, 
	claims_count INTEGER, 
	verified_claims_count INTEGER, 
	latency_ms FLOAT, 
	model_provider VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (audit_id)
);

CREATE INDEX ix_generation_audits_audit_id ON generation_audits (audit_id);

-- Table: historical_memory_snapshots
CREATE TABLE historical_memory_snapshots (
	snapshot_id VARCHAR(64) NOT NULL, 
	target_well_id VARCHAR(64) NOT NULL, 
	cutoff_timestamp VARCHAR(32) NOT NULL, 
	cutoff_depth_md_m FLOAT, 
	eligible_offset_ids_json TEXT NOT NULL, 
	verified_events_count INTEGER, 
	documents_available_count INTEGER, 
	checksum_sha256 VARCHAR(64) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (snapshot_id)
);

CREATE INDEX ix_historical_memory_snapshots_target_well_id ON historical_memory_snapshots (target_well_id);
CREATE INDEX ix_historical_memory_snapshots_snapshot_id ON historical_memory_snapshots (snapshot_id);

-- Table: lookahead_alerts
CREATE TABLE lookahead_alerts (
	alert_id VARCHAR(64) NOT NULL, 
	active_well_id VARCHAR(64) NOT NULL, 
	current_bit_tvdss_m FLOAT NOT NULL, 
	target_formation VARCHAR(64) NOT NULL, 
	horizon_window_m FLOAT NOT NULL, 
	hazard_predicted VARCHAR(64) NOT NULL, 
	risk_score FLOAT NOT NULL, 
	matched_event_id VARCHAR(64), 
	recommended_mitigation TEXT NOT NULL, 
	evidence_citation VARCHAR(255) NOT NULL, 
	driller_response VARCHAR(32), 
	driller_comments TEXT, 
	response_timestamp TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (alert_id)
);

CREATE INDEX ix_lookahead_alerts_active_well_id ON lookahead_alerts (active_well_id);

-- Table: query_plans
CREATE TABLE query_plans (
	plan_id VARCHAR(64) NOT NULL, 
	raw_query TEXT NOT NULL, 
	target_well_id VARCHAR(64), 
	target_formation VARCHAR(64), 
	event_category VARCHAR(64), 
	depth_min_m FLOAT, 
	depth_max_m FLOAT, 
	depth_datum VARCHAR(16), 
	temporal_cutoff VARCHAR(32), 
	intent_type VARCHAR(64), 
	answer_mode VARCHAR(32), 
	is_ambiguous BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (plan_id)
);

CREATE INDEX ix_query_plans_plan_id ON query_plans (plan_id);

-- Table: replay_packets
CREATE TABLE replay_packets (
	id SERIAL NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	packet_index INTEGER NOT NULL, 
	timestamp VARCHAR(32), 
	depth_md_m FLOAT NOT NULL, 
	depth_tvd_m FLOAT NOT NULL, 
	depth_tvdss_m FLOAT NOT NULL, 
	formation_name VARCHAR(64) NOT NULL, 
	rop_m_hr FLOAT, 
	wob_klbs FLOAT, 
	torque_kft_lb FLOAT, 
	spp_psi FLOAT, 
	mud_weight_sg FLOAT, 
	is_drilling BOOLEAN, 
	is_connection BOOLEAN, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_replay_packets_depth_md_m ON replay_packets (depth_md_m);
CREATE INDEX ix_replay_packets_well_id ON replay_packets (well_id);

-- Table: sentinel_evaluation_results
CREATE TABLE sentinel_evaluation_results (
	eval_id VARCHAR(64) NOT NULL, 
	benchmark_name VARCHAR(64), 
	baseline_name VARCHAR(64) NOT NULL, 
	total_questions INTEGER, 
	recall_at_5 FLOAT, 
	precision_at_5 FLOAT, 
	mrr FLOAT, 
	ndcg FLOAT, 
	citation_correctness FLOAT, 
	groundedness_score FLOAT, 
	abstention_correctness FLOAT, 
	avg_latency_ms FLOAT, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (eval_id)
);

CREATE INDEX ix_sentinel_evaluation_results_eval_id ON sentinel_evaluation_results (eval_id);

-- Table: telemetry_sources
CREATE TABLE telemetry_sources (
	source_id VARCHAR(64) NOT NULL, 
	source_name VARCHAR(128) NOT NULL, 
	source_type VARCHAR(32) NOT NULL, 
	source_mode VARCHAR(32) NOT NULL, 
	connection_status VARCHAR(32), 
	endpoint_url VARCHAR(255), 
	is_read_only BOOLEAN, 
	last_heartbeat TIMESTAMP WITHOUT TIME ZONE, 
	config_json TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (source_id)
);

CREATE INDEX ix_telemetry_sources_connection_status ON telemetry_sources (connection_status);
CREATE INDEX ix_telemetry_sources_source_id ON telemetry_sources (source_id);

-- Table: wells
CREATE TABLE wells (
	well_id VARCHAR(64) NOT NULL, 
	uwi VARCHAR(64) NOT NULL, 
	well_name VARCHAR(128) NOT NULL, 
	field_name VARCHAR(64) NOT NULL, 
	operator VARCHAR(64), 
	latitude FLOAT NOT NULL, 
	longitude FLOAT NOT NULL, 
	kb_elevation_m FLOAT NOT NULL, 
	total_depth_md_m FLOAT, 
	total_depth_tvd_m FLOAT, 
	spud_date VARCHAR(32), 
	completion_date VARCHAR(32), 
	well_type VARCHAR(32), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (well_id)
);

CREATE UNIQUE INDEX ix_wells_uwi ON wells (uwi);
CREATE INDEX ix_wells_field_name ON wells (field_name);
CREATE INDEX ix_wells_well_id ON wells (well_id);

-- Table: advisory_evidence
CREATE TABLE advisory_evidence (
	id SERIAL NOT NULL, 
	advisory_id VARCHAR(64) NOT NULL, 
	source_well_id VARCHAR(64) NOT NULL, 
	event_id VARCHAR(64) NOT NULL, 
	doc_id VARCHAR(64), 
	quoted_passage TEXT NOT NULL, 
	correlation_type VARCHAR(32), 
	source_availability_timestamp VARCHAR(32), 
	PRIMARY KEY (id), 
	FOREIGN KEY(advisory_id) REFERENCES advisory_events (advisory_id)
);

CREATE INDEX ix_advisory_evidence_advisory_id ON advisory_evidence (advisory_id);

-- Table: depth_datums
CREATE TABLE depth_datums (
	id SERIAL NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	datum_type VARCHAR(32), 
	kb_elevation_m FLOAT NOT NULL, 
	water_depth_m FLOAT, 
	ground_elevation_m FLOAT, 
	source_citation VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (well_id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);


-- Table: documents
CREATE TABLE documents (
	doc_id VARCHAR(64) NOT NULL, 
	original_filename VARCHAR(255) NOT NULL, 
	file_path VARCHAR(512) NOT NULL, 
	sha256_hash VARCHAR(64) NOT NULL, 
	file_size_bytes INTEGER NOT NULL, 
	mime_type VARCHAR(64), 
	document_type VARCHAR(64), 
	well_id VARCHAR(64), 
	source_id VARCHAR(64), 
	source_date VARCHAR(32), 
	source_url VARCHAR(512), 
	total_pages INTEGER, 
	is_scanned BOOLEAN, 
	status VARCHAR(32), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (doc_id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
);

CREATE INDEX ix_documents_doc_id ON documents (doc_id);
CREATE INDEX ix_documents_status ON documents (status);
CREATE INDEX ix_documents_well_id ON documents (well_id);
CREATE INDEX ix_documents_source_date ON documents (source_date);
CREATE UNIQUE INDEX ix_documents_sha256_hash ON documents (sha256_hash);

-- Table: evaluation_matches
CREATE TABLE evaluation_matches (
	match_id VARCHAR(64) NOT NULL, 
	run_id VARCHAR(64) NOT NULL, 
	ground_truth_event_id VARCHAR(64) NOT NULL, 
	matched_advisory_id VARCHAR(64), 
	lead_distance_m FLOAT, 
	is_true_positive BOOLEAN, 
	match_status VARCHAR(32), 
	PRIMARY KEY (match_id), 
	FOREIGN KEY(run_id) REFERENCES evaluation_runs (run_id)
);

CREATE INDEX ix_evaluation_matches_run_id ON evaluation_matches (run_id);
CREATE INDEX ix_evaluation_matches_match_id ON evaluation_matches (match_id);

-- Table: fault_blocks
CREATE TABLE fault_blocks (
	fault_block_id VARCHAR(64) NOT NULL, 
	field_id VARCHAR(64) NOT NULL, 
	block_name VARCHAR(128) NOT NULL, 
	structural_compartment VARCHAR(64), 
	displacement_throw_m FLOAT, 
	sealing_nature VARCHAR(32), 
	PRIMARY KEY (fault_block_id), 
	FOREIGN KEY(field_id) REFERENCES fields (field_id)
);

CREATE INDEX ix_fault_blocks_field_id ON fault_blocks (field_id);
CREATE INDEX ix_fault_blocks_fault_block_id ON fault_blocks (fault_block_id);

-- Table: formation_tops
CREATE TABLE formation_tops (
	id SERIAL NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	formation_name VARCHAR(64) NOT NULL, 
	top_md_m FLOAT NOT NULL, 
	top_tvdss_m FLOAT NOT NULL, 
	base_tvdss_m FLOAT, 
	lithology_primary VARCHAR(64), 
	confidence_level VARCHAR(16), 
	PRIMARY KEY (id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE INDEX ix_formation_tops_formation_name ON formation_tops (formation_name);
CREATE INDEX ix_formation_tops_well_id ON formation_tops (well_id);
CREATE INDEX ix_formation_tops_top_tvdss_m ON formation_tops (top_tvdss_m);

-- Table: geological_interpretations
CREATE TABLE geological_interpretations (
	id SERIAL NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	formation_name VARCHAR(64) NOT NULL, 
	top_tvdss_m FLOAT NOT NULL, 
	base_tvdss_m FLOAT, 
	source_citation VARCHAR(255) NOT NULL, 
	interpreter_name VARCHAR(128), 
	interpretation_date VARCHAR(32), 
	confidence VARCHAR(32), 
	PRIMARY KEY (id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE INDEX ix_geological_interpretations_well_id ON geological_interpretations (well_id);

-- Table: ground_truth_events
CREATE TABLE ground_truth_events (
	event_id VARCHAR(64) NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	severity VARCHAR(32) NOT NULL, 
	depth_md_m FLOAT NOT NULL, 
	depth_tvdss_m FLOAT NOT NULL, 
	formation_name VARCHAR(64) NOT NULL, 
	timestamp VARCHAR(32), 
	npt_hours FLOAT, 
	narrative TEXT NOT NULL, 
	adjudication_status VARCHAR(64), 
	source_citation VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (event_id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE INDEX ix_ground_truth_events_event_type ON ground_truth_events (event_type);
CREATE INDEX ix_ground_truth_events_well_id ON ground_truth_events (well_id);
CREATE INDEX ix_ground_truth_events_event_id ON ground_truth_events (event_id);

-- Table: normalized_telemetry
CREATE TABLE normalized_telemetry (
	telemetry_id VARCHAR(64) NOT NULL, 
	source_id VARCHAR(64) NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	timestamp VARCHAR(32) NOT NULL, 
	md_m FLOAT NOT NULL, 
	bit_depth_m FLOAT NOT NULL, 
	tvd_m FLOAT, 
	tvdss_m FLOAT, 
	rop_m_hr FLOAT, 
	wob_kn FLOAT, 
	rpm FLOAT, 
	torque_kn_m FLOAT, 
	spp_kpa FLOAT, 
	hookload_kn FLOAT, 
	flow_in_lpm FLOAT, 
	flow_out_pct FLOAT, 
	pit_volume_m3 FLOAT, 
	mud_weight_sg FLOAT, 
	ecd_sg FLOAT, 
	gas_total_pct FLOAT, 
	current_formation VARCHAR(64), 
	formation_top_tvdss_m FLOAT, 
	formation_base_tvdss_m FLOAT, 
	formation_penetration_pct FLOAT, 
	subsurface_corridor_id VARCHAR(64), 
	quality_state VARCHAR(32), 
	is_connection BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (telemetry_id), 
	FOREIGN KEY(source_id) REFERENCES telemetry_sources (source_id)
);

CREATE INDEX ix_normalized_telemetry_source_id ON normalized_telemetry (source_id);
CREATE INDEX ix_normalized_telemetry_current_formation ON normalized_telemetry (current_formation);
CREATE INDEX ix_normalized_telemetry_timestamp ON normalized_telemetry (timestamp);
CREATE INDEX ix_normalized_telemetry_telemetry_id ON normalized_telemetry (telemetry_id);
CREATE INDEX ix_normalized_telemetry_tvdss_m ON normalized_telemetry (tvdss_m);
CREATE INDEX ix_normalized_telemetry_quality_state ON normalized_telemetry (quality_state);
CREATE INDEX ix_normalized_telemetry_wellbore_id ON normalized_telemetry (wellbore_id);
CREATE INDEX ix_normalized_telemetry_md_m ON normalized_telemetry (md_m);

-- Table: operational_advisories
CREATE TABLE operational_advisories (
	advisory_id VARCHAR(64) NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	source_mode VARCHAR(32), 
	timestamp VARCHAR(32) NOT NULL, 
	hazard_type VARCHAR(64) NOT NULL, 
	severity VARCHAR(16), 
	advisory_state VARCHAR(32), 
	title VARCHAR(255) NOT NULL, 
	summary TEXT NOT NULL, 
	rule_id VARCHAR(64), 
	bit_depth_md_m FLOAT NOT NULL, 
	bit_depth_tvdss_m FLOAT NOT NULL, 
	formation_name VARCHAR(64) NOT NULL, 
	telemetry_evidence_json TEXT NOT NULL, 
	historical_evidence_json TEXT NOT NULL, 
	acknowledged_by VARCHAR(64), 
	acknowledged_at TIMESTAMP WITHOUT TIME ZONE, 
	ack_comments TEXT, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (advisory_id), 
	FOREIGN KEY(rule_id) REFERENCES engineering_rule_versions (rule_id)
);

CREATE INDEX ix_operational_advisories_advisory_state ON operational_advisories (advisory_state);
CREATE INDEX ix_operational_advisories_hazard_type ON operational_advisories (hazard_type);
CREATE INDEX ix_operational_advisories_wellbore_id ON operational_advisories (wellbore_id);
CREATE INDEX ix_operational_advisories_advisory_id ON operational_advisories (advisory_id);

-- Table: raw_telemetry_packets
CREATE TABLE raw_telemetry_packets (
	packet_id VARCHAR(64) NOT NULL, 
	source_id VARCHAR(64) NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	raw_payload TEXT NOT NULL, 
	protocol_version VARCHAR(32), 
	source_timestamp VARCHAR(32), 
	reception_timestamp TIMESTAMP WITHOUT TIME ZONE, 
	checksum_sha256 VARCHAR(64) NOT NULL, 
	is_duplicate BOOLEAN, 
	PRIMARY KEY (packet_id), 
	FOREIGN KEY(source_id) REFERENCES telemetry_sources (source_id)
);

CREATE INDEX ix_raw_telemetry_packets_reception_timestamp ON raw_telemetry_packets (reception_timestamp);
CREATE INDEX ix_raw_telemetry_packets_packet_id ON raw_telemetry_packets (packet_id);
CREATE INDEX ix_raw_telemetry_packets_source_id ON raw_telemetry_packets (source_id);
CREATE INDEX ix_raw_telemetry_packets_wellbore_id ON raw_telemetry_packets (wellbore_id);

-- Table: replay_eligibility
CREATE TABLE replay_eligibility (
	id SERIAL NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	eligibility_tier VARCHAR(64), 
	has_drilling_dates BOOLEAN, 
	has_verified_events BOOLEAN, 
	has_definitive_survey BOOLEAN, 
	has_formation_tops BOOLEAN, 
	has_prior_offsets BOOLEAN, 
	exclusion_reason VARCHAR(255), 
	evaluation_notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE UNIQUE INDEX ix_replay_eligibility_well_id ON replay_eligibility (well_id);

-- Table: replay_sessions
CREATE TABLE replay_sessions (
	session_id VARCHAR(64) NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	start_depth_md_m FLOAT NOT NULL, 
	current_depth_md_m FLOAT NOT NULL, 
	end_depth_md_m FLOAT NOT NULL, 
	start_time VARCHAR(32), 
	"current_time" VARCHAR(32), 
	speed_factor FLOAT, 
	status VARCHAR(32), 
	snapshot_id VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (session_id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE INDEX ix_replay_sessions_snapshot_id ON replay_sessions (snapshot_id);
CREATE INDEX ix_replay_sessions_well_id ON replay_sessions (well_id);
CREATE INDEX ix_replay_sessions_status ON replay_sessions (status);
CREATE INDEX ix_replay_sessions_session_id ON replay_sessions (session_id);

-- Table: reservoirs
CREATE TABLE reservoirs (
	reservoir_id VARCHAR(64) NOT NULL, 
	field_id VARCHAR(64) NOT NULL, 
	reservoir_name VARCHAR(128) NOT NULL, 
	primary_formation VARCHAR(64) NOT NULL, 
	lithology VARCHAR(64), 
	avg_porosity_pct FLOAT, 
	avg_permeability_md FLOAT, 
	drive_mechanism VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (reservoir_id), 
	FOREIGN KEY(field_id) REFERENCES fields (field_id)
);

CREATE INDEX ix_reservoirs_field_id ON reservoirs (field_id);
CREATE INDEX ix_reservoirs_reservoir_id ON reservoirs (reservoir_id);

-- Table: source_licences
CREATE TABLE source_licences (
	licence_id VARCHAR(64) NOT NULL, 
	source_id VARCHAR(64) NOT NULL, 
	licence_name VARCHAR(128) NOT NULL, 
	licence_url VARCHAR(255), 
	commercial_allowed BOOLEAN, 
	attribution_text TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (licence_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
);

CREATE INDEX ix_source_licences_licence_id ON source_licences (licence_id);

-- Table: telemetry_channel_mappings
CREATE TABLE telemetry_channel_mappings (
	mapping_id VARCHAR(64) NOT NULL, 
	source_id VARCHAR(64) NOT NULL, 
	source_mnemonic VARCHAR(64) NOT NULL, 
	canonical_name VARCHAR(64) NOT NULL, 
	source_unit VARCHAR(32) NOT NULL, 
	canonical_unit VARCHAR(32) NOT NULL, 
	scale_multiplier FLOAT, 
	offset_value FLOAT, 
	is_measured BOOLEAN, 
	PRIMARY KEY (mapping_id), 
	FOREIGN KEY(source_id) REFERENCES telemetry_sources (source_id)
);

CREATE INDEX ix_telemetry_channel_mappings_source_id ON telemetry_channel_mappings (source_id);
CREATE INDEX ix_telemetry_channel_mappings_mapping_id ON telemetry_channel_mappings (mapping_id);
CREATE INDEX ix_telemetry_channel_mappings_canonical_name ON telemetry_channel_mappings (canonical_name);

-- Table: telemetry_quality_events
CREATE TABLE telemetry_quality_events (
	event_id VARCHAR(64) NOT NULL, 
	source_id VARCHAR(64) NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	issue_type VARCHAR(64) NOT NULL, 
	severity VARCHAR(16), 
	channel_name VARCHAR(64), 
	details_json TEXT NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (event_id), 
	FOREIGN KEY(source_id) REFERENCES telemetry_sources (source_id)
);

CREATE INDEX ix_telemetry_quality_events_issue_type ON telemetry_quality_events (issue_type);
CREATE INDEX ix_telemetry_quality_events_event_id ON telemetry_quality_events (event_id);
CREATE INDEX ix_telemetry_quality_events_wellbore_id ON telemetry_quality_events (wellbore_id);
CREATE INDEX ix_telemetry_quality_events_timestamp ON telemetry_quality_events (timestamp);
CREATE INDEX ix_telemetry_quality_events_source_id ON telemetry_quality_events (source_id);

-- Table: wellbore_surveys
CREATE TABLE wellbore_surveys (
	id SERIAL NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	md_m FLOAT NOT NULL, 
	inclination_deg FLOAT NOT NULL, 
	azimuth_deg FLOAT NOT NULL, 
	tvd_m FLOAT NOT NULL, 
	tvdss_m FLOAT NOT NULL, 
	dogleg_severity_deg_30m FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE INDEX ix_wellbore_surveys_well_id ON wellbore_surveys (well_id);
CREATE INDEX ix_wellbore_surveys_tvdss_m ON wellbore_surveys (tvdss_m);

-- Table: wellbores
CREATE TABLE wellbores (
	wellbore_id VARCHAR(64) NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	wellbore_name VARCHAR(128) NOT NULL, 
	wellbore_type VARCHAR(32), 
	parent_wellbore_id VARCHAR(64), 
	kickoff_depth_md_m FLOAT, 
	total_depth_md_m FLOAT NOT NULL, 
	total_depth_tvdss_m FLOAT NOT NULL, 
	status VARCHAR(32), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (wellbore_id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE INDEX ix_wellbores_wellbore_id ON wellbores (wellbore_id);
CREATE INDEX ix_wellbores_well_id ON wellbores (well_id);

-- Table: advisory_review_events
CREATE TABLE advisory_review_events (
	id SERIAL NOT NULL, 
	advisory_id VARCHAR(64) NOT NULL, 
	old_state VARCHAR(32) NOT NULL, 
	new_state VARCHAR(32) NOT NULL, 
	actor_id VARCHAR(64) NOT NULL, 
	actor_role VARCHAR(64), 
	notes TEXT, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(advisory_id) REFERENCES operational_advisories (advisory_id)
);

CREATE INDEX ix_advisory_review_events_timestamp ON advisory_review_events (timestamp);
CREATE INDEX ix_advisory_review_events_advisory_id ON advisory_review_events (advisory_id);

-- Table: document_pages
CREATE TABLE document_pages (
	id SERIAL NOT NULL, 
	doc_id VARCHAR(64) NOT NULL, 
	page_number INTEGER NOT NULL, 
	raw_text TEXT NOT NULL, 
	is_scanned BOOLEAN, 
	ocr_applied BOOLEAN, 
	ocr_confidence FLOAT, 
	image_path VARCHAR(512), 
	layout_json TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id)
);

CREATE INDEX ix_document_pages_doc_id ON document_pages (doc_id);

-- Table: document_versions
CREATE TABLE document_versions (
	version_id VARCHAR(64) NOT NULL, 
	doc_id VARCHAR(64) NOT NULL, 
	version_number INTEGER, 
	sha256_hash VARCHAR(64) NOT NULL, 
	change_summary VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (version_id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id)
);

CREATE INDEX ix_document_versions_doc_id ON document_versions (doc_id);

-- Table: drilling_events
CREATE TABLE drilling_events (
	event_id VARCHAR(64) NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	severity VARCHAR(16) NOT NULL, 
	depth_md_m FLOAT NOT NULL, 
	depth_tvdss_m FLOAT NOT NULL, 
	formation_name VARCHAR(64) NOT NULL, 
	relative_formation_depth_m FLOAT, 
	npt_hours FLOAT, 
	operational_narrative TEXT NOT NULL, 
	mitigation_applied TEXT, 
	source_citation VARCHAR(255) NOT NULL, 
	event_timestamp VARCHAR(32), 
	verification_status VARCHAR(32), 
	doc_id VARCHAR(64), 
	page_number INTEGER, 
	source_availability_timestamp VARCHAR(32), 
	extraction_method VARCHAR(32), 
	confidence_score FLOAT, 
	reviewed_by VARCHAR(64), 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (event_id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id)
);

CREATE INDEX ix_drilling_events_event_type ON drilling_events (event_type);
CREATE INDEX ix_drilling_events_formation_name ON drilling_events (formation_name);
CREATE INDEX ix_drilling_events_well_id ON drilling_events (well_id);
CREATE INDEX ix_drilling_events_depth_tvdss_m ON drilling_events (depth_tvdss_m);
CREATE INDEX ix_drilling_events_event_id ON drilling_events (event_id);
CREATE INDEX ix_drilling_events_verification_status ON drilling_events (verification_status);

-- Table: extracted_entities
CREATE TABLE extracted_entities (
	id SERIAL NOT NULL, 
	doc_id VARCHAR(64) NOT NULL, 
	page_number INTEGER NOT NULL, 
	entity_type VARCHAR(64) NOT NULL, 
	entity_key VARCHAR(64) NOT NULL, 
	extracted_value VARCHAR(255) NOT NULL, 
	normalized_value FLOAT, 
	unit VARCHAR(32), 
	confidence FLOAT, 
	bbox_json VARCHAR(128), 
	text_passage TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id)
);

CREATE INDEX ix_extracted_entities_entity_type ON extracted_entities (entity_type);
CREATE INDEX ix_extracted_entities_doc_id ON extracted_entities (doc_id);

-- Table: extraction_jobs
CREATE TABLE extraction_jobs (
	job_id VARCHAR(64) NOT NULL, 
	doc_id VARCHAR(64) NOT NULL, 
	status VARCHAR(32), 
	retry_count INTEGER, 
	error_message TEXT, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (job_id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id)
);

CREATE INDEX ix_extraction_jobs_doc_id ON extraction_jobs (doc_id);
CREATE INDEX ix_extraction_jobs_status ON extraction_jobs (status);

-- Table: formation_interpretations
CREATE TABLE formation_interpretations (
	interpretation_id VARCHAR(64) NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	formation_id VARCHAR(64) NOT NULL, 
	version_number INTEGER, 
	interpreter_name VARCHAR(128), 
	source_document_id VARCHAR(64), 
	top_md_m FLOAT NOT NULL, 
	top_tvdss_m FLOAT NOT NULL, 
	base_md_m FLOAT, 
	base_tvdss_m FLOAT, 
	confidence_level VARCHAR(32), 
	uncertainty_m FLOAT, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (interpretation_id), 
	FOREIGN KEY(wellbore_id) REFERENCES wellbores (wellbore_id), 
	FOREIGN KEY(formation_id) REFERENCES formations (formation_id), 
	FOREIGN KEY(source_document_id) REFERENCES documents (doc_id)
);

CREATE INDEX ix_formation_interpretations_interpretation_id ON formation_interpretations (interpretation_id);
CREATE INDEX ix_formation_interpretations_top_tvdss_m ON formation_interpretations (top_tvdss_m);
CREATE INDEX ix_formation_interpretations_formation_id ON formation_interpretations (formation_id);
CREATE INDEX ix_formation_interpretations_wellbore_id ON formation_interpretations (wellbore_id);

-- Table: geological_correlations
CREATE TABLE geological_correlations (
	correlation_id VARCHAR(64) NOT NULL, 
	primary_wellbore_id VARCHAR(64) NOT NULL, 
	offset_wellbore_id VARCHAR(64) NOT NULL, 
	formation_id VARCHAR(64) NOT NULL, 
	correlation_type VARCHAR(32), 
	primary_relative_depth_m FLOAT NOT NULL, 
	offset_relative_depth_m FLOAT NOT NULL, 
	depth_shift_m FLOAT NOT NULL, 
	confidence_score FLOAT, 
	uncertainty_m FLOAT, 
	abstention_flag BOOLEAN, 
	abstention_reason VARCHAR(128), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (correlation_id), 
	FOREIGN KEY(primary_wellbore_id) REFERENCES wellbores (wellbore_id), 
	FOREIGN KEY(offset_wellbore_id) REFERENCES wellbores (wellbore_id), 
	FOREIGN KEY(formation_id) REFERENCES formations (formation_id)
);

CREATE INDEX ix_geological_correlations_correlation_id ON geological_correlations (correlation_id);
CREATE INDEX ix_geological_correlations_offset_wellbore_id ON geological_correlations (offset_wellbore_id);
CREATE INDEX ix_geological_correlations_primary_wellbore_id ON geological_correlations (primary_wellbore_id);
CREATE INDEX ix_geological_correlations_formation_id ON geological_correlations (formation_id);

-- Table: knowledge_chunks
CREATE TABLE knowledge_chunks (
	chunk_id VARCHAR(64) NOT NULL, 
	doc_id VARCHAR(64) NOT NULL, 
	well_id VARCHAR(64) NOT NULL, 
	page_number INTEGER NOT NULL, 
	passage_text TEXT NOT NULL, 
	bounding_box_json VARCHAR(128), 
	formation_name VARCHAR(64), 
	event_category VARCHAR(64), 
	depth_start_md_m FLOAT, 
	depth_end_md_m FLOAT, 
	depth_datum VARCHAR(16), 
	technical_measurements_json TEXT, 
	provenance_tier VARCHAR(32), 
	verification_status VARCHAR(32), 
	sha256_hash VARCHAR(64) NOT NULL, 
	source_date VARCHAR(32), 
	availability_timestamp VARCHAR(32), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (chunk_id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id), 
	FOREIGN KEY(well_id) REFERENCES wells (well_id)
);

CREATE INDEX ix_knowledge_chunks_verification_status ON knowledge_chunks (verification_status);
CREATE INDEX ix_knowledge_chunks_formation_name ON knowledge_chunks (formation_name);
CREATE INDEX ix_knowledge_chunks_well_id ON knowledge_chunks (well_id);
CREATE INDEX ix_knowledge_chunks_provenance_tier ON knowledge_chunks (provenance_tier);
CREATE INDEX ix_knowledge_chunks_doc_id ON knowledge_chunks (doc_id);
CREATE INDEX ix_knowledge_chunks_event_category ON knowledge_chunks (event_category);
CREATE INDEX ix_knowledge_chunks_chunk_id ON knowledge_chunks (chunk_id);

-- Table: lithology_intervals
CREATE TABLE lithology_intervals (
	id SERIAL NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	top_md_m FLOAT NOT NULL, 
	base_md_m FLOAT NOT NULL, 
	lithology_name VARCHAR(64) NOT NULL, 
	porosity_pct FLOAT, 
	source_log VARCHAR(64), 
	PRIMARY KEY (id), 
	FOREIGN KEY(wellbore_id) REFERENCES wellbores (wellbore_id)
);

CREATE INDEX ix_lithology_intervals_wellbore_id ON lithology_intervals (wellbore_id);

-- Table: operational_intervals
CREATE TABLE operational_intervals (
	id SERIAL NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	section_name VARCHAR(64) NOT NULL, 
	top_md_m FLOAT NOT NULL, 
	base_md_m FLOAT NOT NULL, 
	hole_size_in FLOAT NOT NULL, 
	casing_size_in FLOAT, 
	mud_type VARCHAR(64), 
	mud_density_min_sg FLOAT, 
	mud_density_max_sg FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(wellbore_id) REFERENCES wellbores (wellbore_id)
);

CREATE INDEX ix_operational_intervals_wellbore_id ON operational_intervals (wellbore_id);

-- Table: survey_versions
CREATE TABLE survey_versions (
	version_id VARCHAR(64) NOT NULL, 
	wellbore_id VARCHAR(64) NOT NULL, 
	version_number INTEGER, 
	survey_tool VARCHAR(64), 
	survey_company VARCHAR(64), 
	calculation_method VARCHAR(64), 
	is_definitive BOOLEAN, 
	source_citation VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (version_id), 
	FOREIGN KEY(wellbore_id) REFERENCES wellbores (wellbore_id)
);

CREATE INDEX ix_survey_versions_version_id ON survey_versions (version_id);
CREATE INDEX ix_survey_versions_wellbore_id ON survey_versions (wellbore_id);

-- Table: wellbore_relationships
CREATE TABLE wellbore_relationships (
	id SERIAL NOT NULL, 
	parent_wellbore_id VARCHAR(64) NOT NULL, 
	child_wellbore_id VARCHAR(64) NOT NULL, 
	relationship_type VARCHAR(32), 
	kickoff_depth_md_m FLOAT NOT NULL, 
	kickoff_formation VARCHAR(64), 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_wellbore_id) REFERENCES wellbores (wellbore_id), 
	FOREIGN KEY(child_wellbore_id) REFERENCES wellbores (wellbore_id)
);

CREATE INDEX ix_wellbore_relationships_parent_wellbore_id ON wellbore_relationships (parent_wellbore_id);
CREATE INDEX ix_wellbore_relationships_child_wellbore_id ON wellbore_relationships (child_wellbore_id);

-- Table: answer_claims
CREATE TABLE answer_claims (
	claim_id VARCHAR(64) NOT NULL, 
	session_id VARCHAR(64) NOT NULL, 
	claim_text TEXT NOT NULL, 
	claim_type VARCHAR(32), 
	verification_status VARCHAR(32), 
	confidence_score FLOAT, 
	supporting_chunk_id VARCHAR(64), 
	source_citation VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (claim_id), 
	FOREIGN KEY(supporting_chunk_id) REFERENCES knowledge_chunks (chunk_id)
);

CREATE INDEX ix_answer_claims_session_id ON answer_claims (session_id);
CREATE INDEX ix_answer_claims_claim_id ON answer_claims (claim_id);

-- Table: correlation_reviews
CREATE TABLE correlation_reviews (
	review_id VARCHAR(64) NOT NULL, 
	correlation_id VARCHAR(64) NOT NULL, 
	reviewer_name VARCHAR(128) NOT NULL, 
	reviewer_role VARCHAR(64), 
	decision VARCHAR(32) NOT NULL, 
	review_notes TEXT, 
	review_timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (review_id), 
	FOREIGN KEY(correlation_id) REFERENCES geological_correlations (correlation_id)
);

CREATE INDEX ix_correlation_reviews_correlation_id ON correlation_reviews (correlation_id);
CREATE INDEX ix_correlation_reviews_review_id ON correlation_reviews (review_id);

-- Table: event_evidence
CREATE TABLE event_evidence (
	evidence_id VARCHAR(64) NOT NULL, 
	event_id VARCHAR(64) NOT NULL, 
	doc_id VARCHAR(64) NOT NULL, 
	page_number INTEGER NOT NULL, 
	quoted_passage TEXT NOT NULL, 
	bbox_json VARCHAR(128), 
	extraction_method VARCHAR(32), 
	confidence_score FLOAT, 
	evidence_status VARCHAR(32), 
	missing_fields_json TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (evidence_id), 
	FOREIGN KEY(event_id) REFERENCES drilling_events (event_id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id)
);

CREATE INDEX ix_event_evidence_event_id ON event_evidence (event_id);
CREATE INDEX ix_event_evidence_doc_id ON event_evidence (doc_id);
CREATE INDEX ix_event_evidence_evidence_status ON event_evidence (evidence_status);
CREATE INDEX ix_event_evidence_evidence_id ON event_evidence (evidence_id);

-- Table: formation_bottoms
CREATE TABLE formation_bottoms (
	id SERIAL NOT NULL, 
	interpretation_id VARCHAR(64) NOT NULL, 
	formation_id VARCHAR(64) NOT NULL, 
	bottom_md_m FLOAT NOT NULL, 
	bottom_tvdss_m FLOAT NOT NULL, 
	is_proven BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(interpretation_id) REFERENCES formation_interpretations (interpretation_id)
);

CREATE INDEX ix_formation_bottoms_interpretation_id ON formation_bottoms (interpretation_id);

-- Table: survey_stations
CREATE TABLE survey_stations (
	id SERIAL NOT NULL, 
	survey_version_id VARCHAR(64) NOT NULL, 
	station_index INTEGER NOT NULL, 
	md_m FLOAT NOT NULL, 
	inclination_deg FLOAT NOT NULL, 
	azimuth_deg FLOAT NOT NULL, 
	tvd_m FLOAT NOT NULL, 
	tvdss_m FLOAT NOT NULL, 
	northing_m FLOAT, 
	easting_m FLOAT, 
	dogleg_severity_deg_30m FLOAT, 
	is_interpolated BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(survey_version_id) REFERENCES survey_versions (version_id)
);

CREATE INDEX ix_survey_stations_tvdss_m ON survey_stations (tvdss_m);
CREATE INDEX ix_survey_stations_survey_version_id ON survey_stations (survey_version_id);

-- Table: review_tasks
CREATE TABLE review_tasks (
	task_id VARCHAR(64) NOT NULL, 
	doc_id VARCHAR(64) NOT NULL, 
	event_id VARCHAR(64), 
	evidence_id VARCHAR(64), 
	status VARCHAR(32), 
	flag_reason VARCHAR(64) NOT NULL, 
	original_payload_json TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (task_id), 
	FOREIGN KEY(doc_id) REFERENCES documents (doc_id), 
	FOREIGN KEY(event_id) REFERENCES drilling_events (event_id), 
	FOREIGN KEY(evidence_id) REFERENCES event_evidence (evidence_id)
);

CREATE INDEX ix_review_tasks_status ON review_tasks (status);
CREATE INDEX ix_review_tasks_doc_id ON review_tasks (doc_id);
CREATE INDEX ix_review_tasks_event_id ON review_tasks (event_id);
CREATE INDEX ix_review_tasks_task_id ON review_tasks (task_id);

-- Table: review_decisions
CREATE TABLE review_decisions (
	decision_id VARCHAR(64) NOT NULL, 
	task_id VARCHAR(64) NOT NULL, 
	reviewer_id VARCHAR(64) NOT NULL, 
	reviewer_role VARCHAR(64), 
	decision VARCHAR(32) NOT NULL, 
	corrections_json TEXT, 
	comments TEXT, 
	decision_timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (decision_id), 
	FOREIGN KEY(task_id) REFERENCES review_tasks (task_id)
);

CREATE INDEX ix_review_decisions_task_id ON review_decisions (task_id);
