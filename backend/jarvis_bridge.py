import json
import sys
import os

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_ROOT)

from llm.full_jarvis import FullJARVIS


def main():

    input_data = sys.stdin.read()

    if not input_data:
        return

    world_state = json.loads(input_data)

    jarvis = FullJARVIS()

    result = jarvis.generate_report(
        world_state
    )

    print(
        json.dumps(
            result,
            default=str
        )
    )


if __name__ == "__main__":
    main()