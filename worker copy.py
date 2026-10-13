
import pickle
import sys
import zmq
import os

from messages import TaskMessage, ResultMessage


# 1. Read the worker's identity and result port.
if len(sys.argv) != 3:
    print("Usage: python worker.py <worker_id> <result_port>")
    raise SystemExit(1)

worker_id = sys.argv[1]
result_port = int(sys.argv[2])


# 2. Create the ZeroMQ context.
context = zmq.Context()

# 3. Create a PULL socket to receive tasks.
task_receiver = context.socket(zmq.PULL)
distributor_host = os.getenv(
    "DISTRIBUTOR_HOST",
    "127.0.0.1"
)

task_receiver.connect(
    f"tcp://{distributor_host}:9921"
)

# 4. Create a PUSH socket to send results.
result_sender = context.socket(zmq.PUSH)
result_sender.bind(f"tcp://*:{result_port}")
ready_sender = context.socket(zmq.PUSH)
ready_sender.connect(f"tcp://{distributor_host}:9922")

print(f"[{worker_id}] Ready to receive tasks.")
print(f"[{worker_id}] Result endpoint uses port {result_port}.")

try:
    ready_sender.send_string(worker_id)
    print(f"[{worker_id}] Sent readiness signal to distributor.")

    # 5. Receive one serialized task.
    serialized_task = task_receiver.recv()

    # 6. Reconstruct the task object.
    task = pickle.loads(serialized_task)

    if not isinstance(task, TaskMessage):
        raise TypeError("Received an invalid task message.")

    if task.operation != "sum":
        raise ValueError("Unsupported operation.")

    # 7. Perform the calculation.
    result = task.x + task.y

    print(
        f"[{worker_id}] Received task-{task.task_id}: "
        f"{task.x} + {task.y} = {result}"
    )

    # 8. Create the result message.
    result_message = ResultMessage(
        task_id=task.task_id,
        worker_id=worker_id,
        x=task.x,
        y=task.y,
        result=result
    )

    # 9. Serialize and send the result.
    serialized_result = pickle.dumps(result_message)
    result_sender.send(serialized_result)

    print(f"[{worker_id}] Sent result for task-{task.task_id}.")

finally:
    # 10. Release resources.
    task_receiver.close()
    result_sender.close()
    ready_sender.close()
    context.term()
