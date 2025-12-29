{% set y = 2025 %}
{% set m = '{:02d}'.format(8) %}
{% set d = '{:02d}'.format(30) %}
{{ config(
	materialized='view',
	pre_hook=[
		"SET s3_region='us-east-1'",
		"SET s3_access_key_id='minioadmin'",
		"SET s3_secret_access_key='minioadmin'",
		"SET s3_endpoint='localhost:9000'",
		"SET s3_use_ssl='false'",
		"SET s3_url_style='path'",
	],
) }}

select *
from read_parquet('s3://stock-data-local/streaming-output/**/*.parquet')