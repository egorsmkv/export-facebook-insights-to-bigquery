import os
from time import sleep
from os.path import dirname, exists

from google.cloud import bigquery
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

from config import *

# Set the Google's service account 
service_account_file = dirname(__file__) + '/service-account.json'
if not exists(service_account_file):
    exit('The service account file does not exist, goodbye.')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_file

# Init the BigQuery client
client = bigquery.Client()

# Init the Facebook client
FacebookAdsApi.init(fb_app_id, fb_app_secret, fb_access_token)

# Init our AdAccount
ad_account = AdAccount(f'act_{fb_ad_account}')

# Which fields we want to get
insights_fields = [
    'ad_id',
    'adset_id',
    'campaign_id',

    'impressions',
    'spend',
    'reach',
    'clicks',
    'conversions',

    # Facebook API can throw a 500 error if some additional fields are provided, just make a du'a 
    # 'unique_clicks',
    # 'outbound_clicks',
    # 'unique_conversions',

    'date_start',
    'date_stop',
]

# Run exporting
for campaign in ad_account.get_campaigns():
    for ad_set in campaign.get_ad_sets(fields=['name'], params={'date_preset': date_preset}):
        sleep(1)

        for ad in ad_set.get_ads(fields=['name'], params={'date_preset': date_preset}):
            sleep(1)

            print('---')
            for insight in ad.get_insights(fields=insights_fields, params={'date_preset': date_preset}):
                sleep(1)

                ad_id = insight['ad_id']
                adset_id = insight['adset_id']
                campaign_id = insight['campaign_id']
                
                impressions = int(insight['impressions'])
                spend = float(insight['spend'])
                reach = int(insight['reach'])
                clicks = int(insight['clicks'])
                conversions = int(insight['conversions']) if 'conversions' in insight else 0

                date_start = insight['date_start']
                date_stop = insight['date_stop']

                # Generate a query
                q = f"""
                    BEGIN
                        BEGIN TRANSACTION;
                            DELETE FROM `{bigquery_table}` WHERE ad_id = "{ad_id}";
                            INSERT INTO `{bigquery_table}`
                            (ad_id,adset_id,campaign_id,impressions,reach,spend,clicks,conversions,date_start,date_stop)
                                VALUES
                            ("{ad_id}", "{adset_id}", "{campaign_id}", {impressions}, {reach}, {spend}, {clicks}, {conversions}, "{date_start}", "{date_stop}");
                        COMMIT TRANSACTION;

                        EXCEPTION WHEN ERROR THEN
                            SELECT @@error.message;
                        ROLLBACK TRANSACTION;
                    END;
                """.strip()

                print('Executing:')
                print(q)

                # Perform a query
                query_job = client.query(q)

                # Print results
                for row in query_job.result():
                    print(row)
