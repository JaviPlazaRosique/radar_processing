import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.transforms.window import Sessions
import json
import logging
import argparse

parser = argparse.ArgumentParser(description=('Dataflow Streaming Pipeline'))

parser.add_argument('--project_id',
                    required = True,
                    help = 'GCP cloud project id.')

parser.add_argument('--traffic_subscription',
                    required = True,
                    help = 'GCP PubSub subscription for traffic data topic')

args, pipeline_opts = parser.parse_known_args()

def ParsePubSubMessage(message):
    message_str = message.decode('utf-8')

    message_dict = json.loads(message_str)

    logging.info(f"Parsed message {message_dict}")

    return message_dict

def run():
    options = PipelineOptions(pipeline_opts, 
                              streaming = True, 
                              project = args.project_id)
    options.view_as(StandardOptions)

    with beam.Pipeline(argv = pipeline_opts, options = options) as p:

        PubSubMessage = (
            p
            | "ReadFromPubSub" >> beam.io.ReadFromPubSub(
                subscription = f"projects/{args.project_id}/subscriptions/{args.traffic_subscription}"
            )
            | "ParsePubSubMessage" >> beam.Map(ParsePubSubMessage)
        )

        Windows = (
            PubSubMessage
            | "WindowIntoSessions" >> beam.WindowInto(Sessions(gap_size = 1000))
            | "KeyByDriverID" >> beam.Map(lambda x: (x['license_plate'], x)) 
            | "GroupByDriverID" >> beam.GroupByKey()
        ) 

        Windows | beam.Map(print)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)

    logging.info("The process started")

    run()