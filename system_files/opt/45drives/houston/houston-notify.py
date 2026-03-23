import dbus
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description="Send a structured message via Houston D-Bus server.")
    parser.add_argument("message", help="JSON message to forward to Houston (as a string)")
    args = parser.parse_args()

    # Connect to system D-Bus
    bus = dbus.SystemBus()
    remote_object = bus.get_object("org._45drives.Houston", "/org/_45drives/Houston")
    interface = dbus.Interface(remote_object, "org._45drives.Houston")

    # Send the structured message
    response = interface.ForwardMessage(args.message)
    print(f"D-Bus Response (ForwardMessage): {response}")

if __name__ == "__main__":
    main()