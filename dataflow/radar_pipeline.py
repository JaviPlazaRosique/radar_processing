import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.transforms.window import Sessions
from apache_beam.transforms import trigger
from datetime import datetime
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

    if isinstance(message_dict['timestamp'], str):
        dt = datetime.fromisoformat(message_dict['timestamp'].replace('Z', '+00:00'))

        message_dict['timestamp'] = dt

    return beam.window.TimestampedValue(message_dict, message_dict['timestamp'].timestamp())

class SpeedCalculator(beam.DoFn):
    def process(self, element):
        license_plate, events = element

        events_sorted = sorted(events, key = lambda x: x['timestamp'])

        if len(events_sorted) < 2:
            return

        entry_event = events_sorted[0]
        exit_event = events_sorted[-1]

        time_diff = exit_event['timestamp'] - entry_event['timestamp']
        time_in_seconds = time_diff.total_seconds()

        if time_in_seconds <= 0:
            return

        distance_km = 5

        speed_kmh = (distance_km / time_in_seconds) * 3600

        result = {
            'license_plate': license_plate,
            'speed': round(speed_kmh, 2),
        }

        logging.info(f"License Plate: {license_plate}, Speed: {speed_kmh:.2f} km/h")
        yield result

class SpeedLimitViolation(beam.DoFn):
    def process(self, element):
        speed = element['speed']

        limit = 120

        excess_percentage = ((speed - limit) / limit) * 100
        
        violation_data = {
            **element,
            'limit': limit,
            'excess_percentage': round(excess_percentage, 2),
            'fine_amount': 0,
            'points_lost': 0,
            'severity': 'None'
        }

        if excess_percentage > 0:
            if speed <= (limit + 30 if limit >= 100 else limit + 20):
                violation_data.update({'fine_amount': 100, 'points_lost': 0, 'severity': 'Grave'})
            elif excess_percentage < 50:
                violation_data.update({'fine_amount': 300, 'points_lost': 2, 'severity': 'Grave'})
            elif excess_percentage < 60:
                violation_data.update({'fine_amount': 400, 'points_lost': 4, 'severity': 'Grave'})
            elif excess_percentage < 70:
                violation_data.update({'fine_amount': 500, 'points_lost': 6, 'severity': 'Grave'})
            else:
                violation_data.update({'fine_amount': 600, 'points_lost': 6, 'severity': 'Muy Grave'})

        yield violation_data

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
            | "WindowIntoSessions" >> beam.WindowInto(
                Sessions(gap_size = 1000),
                trigger = trigger.Repeatedly(trigger.AfterCount(1)),
                accumulation_mode = trigger.AccumulationMode.ACCUMULATING
                )
            | "KeyByDriverID" >> beam.Map(lambda x: (x['license_plate'], x)) 
            | "GroupByDriverID" >> beam.GroupByKey()
        ) 

        Speed = (
            Windows
            | "CalculateSpeed" >> beam.ParDo(SpeedCalculator())
            | "SpeedLimitViolation" >> beam.ParDo(SpeedLimitViolation())
        )

        Speed | "PrintResults" >> beam.Map(print)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)

    logging.info("The process started")

    run()