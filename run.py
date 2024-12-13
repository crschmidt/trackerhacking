import argparse
from beacons import update_beacons, history, get_latest_observation, history_geojson, insert_from_plist

def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', 'yes', '1'):
        return True
    elif value.lower() in ('false', 'no', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")

def main():
    parser = argparse.ArgumentParser(description="Command Line Utility for Beacon Management")
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update beacons")
    update_parser.set_defaults(func=lambda args: print(update_beacons()))

    # History command
    history_parser = subparsers.add_parser("history", help="Show history of observations")
    history_parser.add_argument("beacon_id", type=int, help="ID of Beacon")
    history_parser.set_defaults(func=lambda args: print(history(args.beacon_id)))
    
    history_geojson_parser = subparsers.add_parser("history_geojson", help="Show history of observations as GeoJSON")
    history_geojson_parser.add_argument("beacon_id", type=int, help="ID of Beacon")
    history_geojson_parser.set_defaults(func=lambda args: print(history_geojson(args.beacon_id)))

    # Insert from plist
    insert_parser = subparsers.add_parser("insert")
    insert_parser.add_argument("name", type=str)
    insert_parser.add_argument("plist", type=str)
    insert_parser.set_defaults(func=lambda args: print(insert_from_plist(args.name, args.plist)))

    # Latest command
    latest_parser = subparsers.add_parser("latest", help="Get latest observation")
    latest_parser.add_argument("number", type=int, help="Number of latest observations to retrieve")
    latest_parser.add_argument(
        "--update",
        type=str_to_bool,
        default=True,
        help="Whether to update the observation (True/False, default: True)",
    )
    latest_parser.set_defaults(
        func=lambda args: print(get_latest_observation(args.number, update=args.update))
    )

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

