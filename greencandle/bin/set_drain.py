"""
Script for manually setting drain status for all envs/containers
"""
from greencandle.lib.web import set_drain
from greencandle.lib.common import arg_decorator


@arg_decorator
def main():
    """
    Prompt for drain details then set status via drain api
    """

    print("1. top level drain")
    print("2. partial drain")
    drain_type = input("Select drain type: ")

    env = input("Enter Env: ")
    direction = input("Enter direction: ")

    if drain_type.strip() == "2":
        interval = input("Enter interval: ")
    else:
        interval = None

    value = input("Enter value (true/false): ")

    set_drain(env=env, interval=interval, value=value, direction=direction)

    print(env, interval, direction, value)


if __name__ == '__main__':
    main()
