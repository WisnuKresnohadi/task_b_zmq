
import random
import pickle
import zmq

from messages import TaskMessage


# 1. Create the ZeroMQ context.
context = zmq.Context()

# 2. Create a PUSH socket to distribute tasks.
task_sender = context.socket(zmq.PUSH)
task_sender.bind("tcp://*:9921")

# 3. Create a PULL socket for readiness and completion messages.
ready_receiver = context.socket(zmq.PULL)
ready_receiver.bind("tcp://*:9922")

# 4. Define the expected participants.
expected_participants = {
    "Worker 1",
    "Worker 2",
    "Collector",
}

expected_workers = {
    "Worker 1",
    "Worker 2",
}

ready_participants = set()
completed_workers = set()

print(
    "[Distributor] Waiting for both workers "
    "and the collector to be ready."
)

try:
    # 5. Wait for all participants to report readiness.
    while ready_participants != expected_participants:
        participant = ready_receiver.recv_string()

        if (
            participant in expected_participants
            and participant not in ready_participants
        ):
            ready_participants.add(participant)

            print(
                f"[Distributor] {participant} is ready "
                f"({len(ready_participants)}/3)."
            )

    print("[Distributor] All participants are ready.")

    # 6. Generate two random integers.
    x = random.randint(1, 100)
    y = random.randint(1, 100)

    print(f"[Distributor] Generated x={x}, y={y}")

    # 7. Send two tasks to the workers.
    for task_id in range(1, 3):
        task = TaskMessage(
            task_id=task_id,
            x=x,
            y=y,
        )

        serialized_task = pickle.dumps(task)
        task_sender.send(serialized_task)

        print(
            f"[Distributor] Sent task-{task_id}: "
            f"{x} + {y}"
        )

    # 8. Wait for both workers to finish processing.
    print(
        "[Distributor] Waiting for completion "
        "acknowledgments from both workers."
    )

    while completed_workers != expected_workers:
        message = ready_receiver.recv_string()

        if message.startswith("DONE|"):
            worker_id = message.partition("|")[2]

            if (
                worker_id in expected_workers
                and worker_id not in completed_workers
            ):
                completed_workers.add(worker_id)

                print(
                    f"[Distributor] Received completion "
                    f"from {worker_id} "
                    f"({len(completed_workers)}/2)."
                )

    print("[Distributor] Both workers have completed their tasks.")

finally:
    # 9. Release resources.
    task_sender.close()
    ready_receiver.close()
    context.term()

print("[Distributor] Finished successfully.")
